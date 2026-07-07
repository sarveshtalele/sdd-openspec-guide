"""
Code-Behind Method Extractor
============================
Extracts per-method business-logic skeletons from ASP.NET Web Forms
code-behind (.cs) so the consolidated report can emit the client's required
format WITHOUT the AI having to re-read 10000+ source files:

    File Name / Class Name / Method Name / Method Purpose /
    Detailed Business Logic / Validation & Conditional Rules /
    Called Components & Dependencies / Data Flow & Mappings

Pure regex + brace-matching. Tolerant of malformed/partial code.
Operates on a single file's text and returns small dicts — never holds
multiple file bodies, so it is safe for streaming over huge repos.
"""

import re
from typing import Dict, List, Any

# ---- method signature: visibility + modifiers + return type + name(params) {
_METHOD_SIG = re.compile(
    r'(?P<vis>public|private|protected|internal)\s+'
    r'(?P<mods>(?:static\s+|virtual\s+|override\s+|async\s+|sealed\s+|new\s+)*)'
    r'(?P<ret>[\w<>\[\],.\s?]+?)\s+'
    r'(?P<name>\w+)\s*'
    r'\((?P<params>[^;{)]*)\)\s*'
    r'(?:where[^{;]+)?'
    r'\{',
    re.MULTILINE,
)

_EVENT_SUFFIX = (
    'Click', 'Change', 'SelectedIndexChanged', 'Command', 'DataBound',
    'ItemCommand', 'RowCommand', 'CheckedChanged', 'TextChanged',
    'RowDeleting', 'RowEditing', 'RowUpdating', 'RowCancelingEdit',
    'PreRender', 'Load', 'Init', 'Unload', 'ItemDataBound', 'Sorting',
    'PageIndexChanging', 'NeedDataSource',
)

# ---- fact patterns (run against a single method body) ---------------------
_P_SESSION_W   = re.compile(r'Session\s*\[\s*"([^"]+)"\s*\]\s*=', re.I)
_P_SESSION_R   = re.compile(r'Session\s*\[\s*"([^"]+)"\s*\]', re.I)
_P_REQUEST     = re.compile(r'Request(?:\.QueryString|\.Form|\.Params)?\s*\[\s*"([^"]+)"\s*\]', re.I)
_P_VIEWSTATE   = re.compile(r'ViewState\s*\[\s*"([^"]+)"\s*\]', re.I)
_P_APPSETTING  = re.compile(r'(?:ConfigurationManager|WebConfigurationManager)\.AppSettings\s*\[\s*"([^"]+)"\s*\]', re.I)
_P_CONNSTR     = re.compile(r'ConnectionStrings\s*\[\s*"([^"]+)"\s*\]', re.I)
_P_REDIRECT    = re.compile(r'Response\.Redirect\s*\(\s*"([^"]+)"', re.I)
_P_TRANSFER    = re.compile(r'Server\.Transfer\s*\(\s*"([^"]+)"', re.I)
_P_REDIR_VAR   = re.compile(r'Response\.Redirect\s*\(\s*([A-Za-z_]\w*)', re.I)
_P_SQL_OBJ     = re.compile(r'\bnew\s+(SqlCommand|SqlConnection|OleDbCommand|SqlDataAdapter)\b', re.I)
_P_STOREDPROC  = re.compile(r'CommandType\.StoredProcedure', re.I)
_P_SP_NAME     = re.compile(r'(?:CommandText\s*=\s*"|Execute\w*\s*\(\s*"|new\s+SqlCommand\s*\(\s*")([A-Za-z_][\w\.\[\]]*)"', re.I)
_P_SQL_EXEC    = re.compile(r'\.(ExecuteNonQuery|ExecuteReader|ExecuteScalar|Fill)\s*\(', re.I)
_P_LINQ        = re.compile(r'\.(Where|FirstOrDefault|SingleOrDefault|ToList|Select|Find|Add|Remove|SaveChanges|Update)\s*\(', re.I)
_P_VALIDATOR   = re.compile(r'\b(Page\.IsValid|IsValid|RequiredFieldValidator|RegularExpressionValidator|RangeValidator|CompareValidator|CustomValidator|ModelState\.IsValid)\b')
_P_GUARD       = re.compile(r'\b(string\.IsNullOrEmpty|string\.IsNullOrWhiteSpace|int\.TryParse|decimal\.TryParse|DateTime\.TryParse|\.HasValue|== null|!= null)\b')
_P_THROW       = re.compile(r'\bthrow\s+new\s+(\w+)', re.I)
_P_IF          = re.compile(r'\bif\s*\(')
_P_ELSE        = re.compile(r'\belse\b')
_P_SWITCH      = re.compile(r'\bswitch\s*\(')
_P_LOOP        = re.compile(r'\b(for|foreach|while)\s*\(')
_P_TRY         = re.compile(r'\btry\b')
_P_NEW_OBJ     = re.compile(r'\bnew\s+([A-Z]\w+)\s*\(')
_P_STATIC_CALL = re.compile(r'\b([A-Z][A-Za-z0-9_]+)\.([A-Z][A-Za-z0-9_]+)\s*\(')
_P_CTRL_READ   = re.compile(r'\b(\w+)\.(Text|SelectedValue|SelectedItem|Checked|Value)\b')
_P_CTRL_WRITE  = re.compile(r'\b(\w+)\.(Text|Visible|Enabled|DataSource)\s*=')
_P_CALC        = re.compile(r'[\w\)\]]\s*[\*/%+\-]\s*[\w\(]')  # arithmetic hint
_P_EMAIL       = re.compile(r'\b(SmtpClient|MailMessage|SendEmail|SendMail)\b', re.I)

# framework/noise types to exclude from "called components"
_NOISE_TYPES = {
    'String', 'Convert', 'Console', 'Math', 'DateTime', 'Int32', 'Decimal',
    'Boolean', 'Guid', 'List', 'Dictionary', 'StringBuilder', 'Exception',
    'Response', 'Request', 'Session', 'Server', 'Page', 'ViewState', 'Array',
    'Enumerable', 'Path', 'File', 'Directory', 'Regex', 'Encoding', 'Type',
    'Object', 'Tuple', 'Task', 'Trace', 'Debug', 'Activator', 'Nullable',
    'TimeSpan', 'Double', 'Single', 'Byte', 'Char', 'Uri', 'Color',
}


def _match_brace_body(text: str, open_idx: int, cap: int = 8000) -> str:
    """Return body between matched braces starting at open_idx (the '{')."""
    depth = 0
    end = open_idx
    n = len(text)
    for i in range(open_idx, min(n, open_idx + 200000)):
        c = text[i]
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                end = i
                break
    return text[open_idx + 1:end][:cap]


def _uniq(seq):
    return list(dict.fromkeys(seq))


def _purpose(name: str, is_event: bool, ctrl: str, evt: str, body: str) -> str:
    n = name.lower()
    if name == 'Page_Load':
        return 'Page initialization — runs on every request; sets up the screen and loads initial data.'
    if name == 'Page_Init':
        return 'Early page initialization (control setup before load).'
    if is_event and evt:
        verb = {
            'Click': 'Handles the user clicking', 'Command': 'Handles a command from',
            'SelectedIndexChanged': 'Reacts to a selection change in',
            'TextChanged': 'Reacts to text input change in',
            'CheckedChanged': 'Reacts to a checkbox/radio change in',
            'RowCommand': 'Handles a row action in', 'ItemCommand': 'Handles an item action in',
            'RowDeleting': 'Handles row deletion in', 'RowEditing': 'Handles entering edit mode in',
            'RowUpdating': 'Handles saving a row edit in', 'DataBound': 'Runs after data binding of',
            'PageIndexChanging': 'Handles paging in',
        }.get(evt, f'Handles the {evt} event of')
        return f'{verb} `{ctrl}` — triggers the associated business action.'
    if n.startswith(('save', 'insert', 'add', 'create')):
        return 'Persists a new record / saves data.'
    if n.startswith(('update', 'edit', 'modify')):
        return 'Updates an existing record.'
    if n.startswith(('delete', 'remove')):
        return 'Deletes / removes a record.'
    if n.startswith(('get', 'load', 'fetch', 'retrieve', 'bind', 'populate', 'fill')):
        return 'Retrieves data and/or binds it to the UI.'
    if n.startswith(('validate', 'check', 'verify', 'is')):
        return 'Validation / business-rule check.'
    if n.startswith(('calc', 'compute', 'total', 'sum')):
        return 'Performs a calculation.'
    return 'Helper / business method.'


def extract_methods(cb_content: str, max_methods: int = 60) -> List[Dict[str, Any]]:
    """Extract compact per-method business-logic facts from code-behind text."""
    if not cb_content:
        return []

    methods: List[Dict[str, Any]] = []
    for m in _METHOD_SIG.finditer(cb_content):
        if len(methods) >= max_methods:
            break
        name = m.group('name')
        ret  = m.group('ret').strip()
        # skip property accessors / constructors-like noise picked up accidentally
        if name in ('if', 'for', 'foreach', 'while', 'switch', 'using', 'lock', 'catch'):
            continue
        body = _match_brace_body(cb_content, m.end() - 1)

        evt = ''
        ctrl = ''
        is_event = '_' in name and name.split('_')[-1] in _EVENT_SUFFIX
        if is_event:
            ctrl, evt = name.rsplit('_', 1)

        # ---- data flow ----
        sess_w = _uniq(_P_SESSION_W.findall(body))
        sess_r = [s for s in _uniq(_P_SESSION_R.findall(body)) if s not in sess_w]
        req    = _uniq(_P_REQUEST.findall(body))
        vstate = _uniq(_P_VIEWSTATE.findall(body))
        appcfg = _uniq(_P_APPSETTING.findall(body))
        conns  = _uniq(_P_CONNSTR.findall(body))
        redirs = _uniq(_P_REDIRECT.findall(body) + _P_TRANSFER.findall(body))
        ctrl_w = _uniq([f'{a}.{b}' for a, b in _P_CTRL_WRITE.findall(body)])
        ctrl_r = _uniq([f'{a}.{b}' for a, b in _P_CTRL_READ.findall(body)])

        # ---- data access ----
        sps    = _uniq([s for s in _P_SP_NAME.findall(body)])
        has_sql = bool(_P_SQL_OBJ.search(body) or _P_SQL_EXEC.search(body))
        is_sproc = bool(_P_STOREDPROC.search(body))
        linq   = _uniq([x for x in _P_LINQ.findall(body)])

        # ---- validation / conditionals ----
        validators = _uniq(_P_VALIDATOR.findall(body))
        guards     = _uniq(_P_GUARD.findall(body))
        throws     = _uniq(_P_THROW.findall(body))
        n_if   = len(_P_IF.findall(body))
        n_else = len(_P_ELSE.findall(body))
        n_sw   = len(_P_SWITCH.findall(body))
        n_loop = len(_P_LOOP.findall(body))
        has_try = bool(_P_TRY.search(body))
        has_calc = bool(_P_CALC.search(body))

        # ---- called components ----
        new_objs = [t for t in _P_NEW_OBJ.findall(body) if t not in _NOISE_TYPES]
        statics  = [t for t, _meth in _P_STATIC_CALL.findall(body)
                    if t not in _NOISE_TYPES and t != name]
        called = _uniq(new_objs + statics)
        # heuristic: classify by suffix
        deps = []
        for c in called[:25]:
            kind = ('repository' if c.lower().endswith(('repository', 'repo', 'dal', 'dao'))
                    else 'service'  if c.lower().endswith(('service', 'manager', 'provider', 'bll', 'facade'))
                    else 'helper'   if c.lower().endswith(('helper', 'util', 'utils', 'utility'))
                    else 'class')
            deps.append({'name': c, 'kind': kind})

        emails = bool(_P_EMAIL.search(body))

        methods.append({
            'name': name,
            'return_type': ret,
            'params': m.group('params').strip(),
            'is_event': is_event,
            'event_control': ctrl,
            'event_type': evt,
            'purpose': _purpose(name, is_event, ctrl, evt, body),
            # data flow
            'session_writes': sess_w, 'session_reads': sess_r,
            'request_inputs': req, 'viewstate': vstate,
            'app_settings': appcfg, 'connection_strings': conns,
            'redirects': redirs, 'control_writes': ctrl_w[:15], 'control_reads': ctrl_r[:15],
            # data access
            'has_sql': has_sql, 'is_stored_proc': is_sproc,
            'stored_procs': sps[:10], 'orm_ops': linq[:10],
            'sends_email': emails,
            # validation / conditionals
            'validators': validators, 'guards': guards, 'throws': throws,
            'if_count': n_if, 'else_count': n_else, 'switch_count': n_sw,
            'loop_count': n_loop, 'has_try': has_try, 'has_calc': has_calc,
            # dependencies
            'dependencies': deps,
        })

    return methods


def method_significance(meth: Dict[str, Any]) -> int:
    """Score a method's business importance for ranking/selection."""
    s = 0
    if meth['is_event']:        s += 4
    if meth['has_sql']:         s += 4
    if meth['stored_procs']:    s += 3
    if meth['orm_ops']:         s += 2
    if meth['validators']:      s += 3
    if meth['guards']:          s += 1
    if meth['redirects']:       s += 1
    if meth['session_writes']:  s += 1
    if meth['sends_email']:     s += 2
    if meth['has_calc']:        s += 1
    s += min(meth['if_count'], 5)
    s += len(meth['dependencies'])
    return s
