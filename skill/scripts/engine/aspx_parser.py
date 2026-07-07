"""
ASPX Parser
===========
Extracts structured metadata from ASP.NET Web Forms markup and code-behind files.
Uses regex rather than XML parsing to tolerate malformed/partial markup common
in large legacy Web Forms repos.

parse_aspx_page()   — .aspx files + .aspx.cs code-behind
parse_ascx_control() — .ascx user controls + .ascx.cs
parse_master_page()  — .master files + .master.cs
parse_web_config()   — authentication, connection strings, location access rules
"""

import re
from pathlib import Path
from typing import Dict, List, Any

# ---------------------------------------------------------------------------
# Compiled patterns — directive level
# ---------------------------------------------------------------------------

_PAGE_DIR = re.compile(
    r'<%@\s*(?:Page|Control|Master)\s+([^%]+?)%>',
    re.DOTALL | re.IGNORECASE,
)
_REGISTER_DIR = re.compile(
    r'<%@\s*Register\s+([^%]+?)%>',
    re.DOTALL | re.IGNORECASE,
)
_ATTR_KV = re.compile(r'(\w+)\s*=\s*"([^"]*)"', re.IGNORECASE)

# ---------------------------------------------------------------------------
# Compiled patterns — markup controls
# ---------------------------------------------------------------------------

_ASPNET_TAG = re.compile(
    # Prefix-agnostic: matches <asp:Button>, <ej:Grid>, <telerik:RadGrid>,
    # <dx:ASPxGridView>, or any other <TagPrefix:TagName> — third-party
    # control libraries (Syncfusion, Telerik, DevExpress, Infragistics, ...)
    # register their own TagPrefix via <%@ Register %> and are just as much
    # "server controls" as the built-in asp: namespace. Classification below
    # keys off the tag NAME only (group 1), so this doesn't change behavior
    # for repos that only use asp:* — it only stops silently dropping every
    # control from a third-party library, which a hardcoded 'asp:' prefix
    # was doing on any repo built on one (this one included).
    r'<\w+:(\w+)\b([^>]*?)(?:/>|>)',
    re.IGNORECASE | re.DOTALL,
)
_ID_ATTR       = re.compile(r'\bID\s*=\s*"([^"]+)"',             re.IGNORECASE)
_TEXT_ATTR     = re.compile(r'\bText\s*=\s*"([^"]+)"',           re.IGNORECASE)
_NAV_URL       = re.compile(r'\bNavigateUrl\s*=\s*(?:"([^"]+)"|\'([^\']+)\')', re.IGNORECASE)
_ANCHOR_HREF   = re.compile(r'<a\b[^>]*\bhref\s*=\s*"([^"]+)"',        re.IGNORECASE)
_ROUTE_URL     = re.compile(
    r'(?:RouteUrl:RouteName=|GetRouteUrl\s*\(\s*["\'])(\w+)',
    re.IGNORECASE,
)
# Separate full-content scan for NavigateUrl attrs containing route expressions.
# Needed because _ASPNET_TAG's [^>]*? truncates at > inside <%# %> expressions,
# which cuts off the closing quote of single-quoted attribute values.
_NAVURL_ROUTE  = re.compile(
    r'\bNavigateUrl\s*=\s*'
    r'(?:\'([^\']*(?:RouteUrl|GetRouteUrl)[^\']*)\''
    r'|"([^"]*(?:RouteUrl|GetRouteUrl)[^"]*)")',
    re.IGNORECASE,
)
_CONTENT_PH    = re.compile(
    r'<asp:ContentPlaceHolder\b[^>]*\bID\s*=\s*"([^"]+)"', re.IGNORECASE
)
_CONTENT_AREA  = re.compile(
    r'<asp:Content\b[^>]*\bContentPlaceHolderID\s*=\s*"([^"]+)"', re.IGNORECASE
)

_FORM_CTRL_TYPES = {
    'button', 'linkbutton', 'imagebutton',
    'textbox', 'dropdownlist', 'listbox', 'checkbox', 'checkboxlist',
    'radiobuttonlist', 'radiobutton', 'fileupload', 'hiddenfield',
    'calendar', 'multiview', 'wizard', 'panel',
    'gridview', 'detailsview', 'formview', 'listview', 'repeater',
    'datalist', 'datagrid',
    'grid',  # Syncfusion EJ1/EJ2's own grid tag name (<ej:Grid>/<ejs:Grid>) —
             # not an asp:* control, but functionally identical to gridview
             # for has_grid/purpose-inference purposes once the tag-prefix
             # regex above stops ignoring non-asp: prefixes.
    'requiredfieldvalidator', 'rangevalidator', 'comparevalidator',
    'regularexpressionvalidator', 'customvalidator', 'validationsummary',
}
_DISPLAY_CTRL_TYPES = {'label', 'literal', 'image', 'bulletedlist'}
_DATA_SRC_TYPES = {
    'sqldatasource', 'objectdatasource', 'entitydatasource',
    'linqdatasource', 'xmldatasource', 'sitemapdatasource',
}
_AJAX_TYPES = {'scriptmanager', 'updatepanel', 'timer', 'asyncpostbacktrigger'}
_LOGIN_TYPES = {'login', 'loginname', 'loginview', 'loginstatus', 'createuserwizard',
                'passwordrecovery', 'changepassword'}
_NAV_CTRL_TYPES = {'menu', 'treeview', 'sitemappath', 'breadcrumb'}

# ---------------------------------------------------------------------------
# Compiled patterns — code-behind
# ---------------------------------------------------------------------------

_CLASS_DECL   = re.compile(
    r'public\s+partial\s+class\s+(\w+)\s*(?::\s*([\w.]+))?', re.MULTILINE
)
_NAMESPACE    = re.compile(r'namespace\s+([\w.]+)',            re.MULTILINE)
_USING        = re.compile(r'^using\s+([\w.]+)\s*;',           re.MULTILINE)
_PAGE_LOAD    = re.compile(r'void\s+Page_Load\s*\(',           re.IGNORECASE)
_PAGE_INIT    = re.compile(r'void\s+Page_Init\s*\(',           re.IGNORECASE)

_EVENT_HANDLER = re.compile(
    r'(?:protected|private|public)\s+void\s+'
    r'(\w+)_(Click|Change|SelectedIndexChanged|Command|DataBound|'
    r'ItemCommand|RowCommand|CheckedChanged|TextChanged|'
    r'RowDeleting|RowEditing|RowUpdating|RowCancelingEdit|'
    r'Load|PreRender|Init|Unload)\s*\(',
    re.IGNORECASE,
)
_REDIRECT     = re.compile(r'Response\.Redirect\s*\(\s*"([^"]+)"',  re.IGNORECASE)
_TRANSFER     = re.compile(r'Server\.Transfer\s*\(\s*"([^"]+)"',    re.IGNORECASE)
_SQL_DIRECT   = re.compile(r'SqlConnection|OleDbConnection|SqlCommand', re.IGNORECASE)
_IS_IN_ROLE   = re.compile(r'User\.IsInRole\s*\(\s*"([^"]+)"',      re.IGNORECASE)
_AUTHORIZE    = re.compile(r'\[Authorize\b([^\]]*)\]',               re.IGNORECASE)
_AUTH_ROLE    = re.compile(r'Roles\s*=\s*"([^"]+)"',                re.IGNORECASE)
_IS_AUTH      = re.compile(r'Request\.IsAuthenticated',              re.IGNORECASE)

# ---------------------------------------------------------------------------
# Domain subject inference — folders / path segments to skip
# ---------------------------------------------------------------------------

_SUBJECT_SKIP = {
    'src', 'app', 'ui', 'web', 'forms', 'pages', 'views', 'areas',
    'modules', 'controls', 'shared', 'common', 'helpers', 'extensions',
    'website', 'wwwroot', '',
}

# ---------------------------------------------------------------------------
# Functional area keyword map
# ---------------------------------------------------------------------------

_AREA_KEYWORDS: Dict[str, List[str]] = {
    'Authentication':  ['login', 'logout', 'register', 'signup', 'password',
                        'auth', 'signin', 'forgotpassword', 'resetpassword',
                        'changepassword', 'account/login', 'account/register'],
    'Administration':  ['admin', 'administration', 'manage', 'management',
                        'dashboard', 'controlpanel', 'backoffice', 'backend'],
    'Reports':         ['report', 'reports', 'statistics', 'analytics',
                        'export', 'chart', 'graph', 'summary', 'insight'],
    'Products':        ['product', 'catalog', 'category', 'item', 'inventory',
                        'sku', 'stock', 'catalogue'],
    'Orders':          ['order', 'cart', 'checkout', 'payment', 'invoice',
                        'purchase', 'billing', 'basket', 'transaction'],
    'Users':           ['user', 'member', 'profile', 'settings', 'preference',
                        'account', 'myaccount', 'customer'],
    'Content':         ['article', 'blog', 'news', 'content', 'cms', 'post',
                        'page', 'media'],
    'Search':          ['search', 'find', 'browse', 'filter', 'results', 'query'],
    'Configuration':   ['config', 'setting', 'setup', 'wizard', 'install',
                        'configure', 'option'],
    'Errors':          ['error', '404', '500', 'exception', 'notfound',
                        'unauthorized', 'accessdenied', 'forbidden'],
    'Home':            ['home', 'index', 'default', 'landing', 'welcome', 'main'],
    'Contact':         ['contact', 'feedback', 'support', 'help', 'faq', 'about'],
    'Shipping':        ['ship', 'shipping', 'delivery', 'address', 'warehouse'],
    'Finance':         ['payment', 'invoice', 'refund', 'credit', 'debit',
                        'financial', 'accounting', 'tax'],
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_attrs(text: str) -> Dict[str, str]:
    return {k.lower(): v for k, v in _ATTR_KV.findall(text)}


# Splits camelCase/PascalCase identifiers at lower->upper transitions so keyword
# matching can find whole words inside concatenated names like "OrderHistory"
# ("order history") without also matching inside plain compound words like
# "Border" or "Reorder" (single case-run, no transition — correctly NOT split).
_CAMEL_SPLIT = re.compile(r'(?<=[a-z0-9])(?=[A-Z])')


def _tokenize(text: str) -> str:
    return _CAMEL_SPLIT.sub(' ', text).lower()


def _kw_match(text: str, keywords: List[str]) -> bool:
    """Whole-word keyword match against already-tokenized (camelCase-split,
    lowercased) text. Plain substring matching here previously misclassified
    e.g. 'Border.aspx' into the 'Orders' functional area, because 'order' is
    a literal substring of 'border' — word-boundary regex on tokenized text
    fixes that without losing legitimate matches like 'OrderHistory' -> 'order
    history' (tokenizing inserts the boundary camelCase already implied)."""
    return any(re.search(rf'\b{re.escape(kw)}\b', text) for kw in keywords)


def _infer_subject(name: str, folder: str, imports: List[str]) -> str:
    """Best-effort domain subject from folder path (e.g. 'Catalog', 'Orders')."""
    parts = folder.replace('\\', '/').split('/')
    for part in reversed(parts):
        p_low = part.lower()
        if (p_low not in _SUBJECT_SKIP
                and not p_low.endswith('solution')
                and not p_low.endswith('webforms')
                and len(part) > 2):
            return part
    return ''


def _infer_functional_area(name: str, folder: str, imports: List[str]) -> str:
    combined = _tokenize(name + ' ' + folder.replace('\\', '/').replace('/', ' '))
    for area, keywords in _AREA_KEYWORDS.items():
        if _kw_match(combined, keywords):
            return area
    # Try imports as a last resort
    imports_str = _tokenize(' '.join(imports))
    for area, keywords in _AREA_KEYWORDS.items():
        if _kw_match(imports_str, keywords):
            return area
    return 'General'


def _infer_page_purpose(name: str, folder: str, ctrl_types: set, has_grid: bool,
                        has_form: bool, imports: List[str] = None) -> str:
    n = name.lower()
    folder_low = folder.lower()
    hint = _infer_subject(name, folder, imports or [])

    if 'login' in n or 'signin' in n:
        return 'User authentication — login form'
    if 'logout' in n or 'signout' in n:
        return 'Session termination / logout'
    if 'register' in n or 'signup' in n:
        return 'New user registration'
    if 'forgotpassword' in n or 'resetpassword' in n:
        return 'Password recovery / reset'
    if 'changepassword' in n:
        return 'Password change form'
    if n in {'default', 'index', 'home', 'main', 'landing'}:
        return 'Application home page / dashboard'
    if 'search' in n:
        subject = re.sub(r'(?i)\bSearches?\b', '', name).strip() or hint or 'records'
        return f'Search interface for {subject}'
    if 'list' in n or has_grid:
        subject = re.sub(r'(?i)\bLists?\b|\bGrids?\b', '', name).strip() or hint or 'records'
        return f'Data list / grid view — {subject}'
    if 'edit' in n or 'form' in n:
        subject = re.sub(r'(?i)\bEdits?\b|\bForms?\b', '', name).strip() or hint or 'record'
        return f'Edit / data entry form — {subject}'
    if 'view' in n or 'detail' in n:
        subject = re.sub(r'(?i)\bDetails?\b|\bViews?\b', '', name).strip() or hint or 'record'
        return f'Detail / read-only view — {subject}'
    if 'create' in n or 'add' in n or 'new' in n:
        subject = re.sub(r'(?i)\b(?:create|add|new)\b', '', name).strip() or hint or 'record'
        return f'Create new {subject}'
    if 'delete' in n or 'remove' in n:
        subject = hint or name
        return f'Delete / remove confirmation — {subject}'
    if 'report' in n:
        return f'Report output — {name.replace("Report", "").strip()}'
    if 'admin' in n or 'admin' in folder_low:
        return f'Administration interface — {name}'
    if 'error' in n or n in {'404', '500', 'accessdenied', 'forbidden'}:
        return 'Error handling page'
    if has_form and has_grid:
        return f'Search-and-list page — {name}'
    if has_form:
        return f'Data entry / form — {name}'
    if has_grid:
        return f'Data listing — {name}'
    return f'{name} page'


def _infer_auth(name: str, folder: str, cb: str) -> str:
    n = name.lower()
    folder_low = folder.lower().replace('\\', '/') + '/' + n

    # Anonymous pages (login, register, error)
    if any(kw in n for kw in ['login', 'register', 'signup', 'forgotpassword',
                               'resetpassword', 'error', '404', '500', 'about',
                               'contact', 'default', 'home', 'index']):
        return 'anonymous'

    if not cb:
        # Admin folder heuristic without code-behind
        if 'admin' in folder_low:
            return 'role:Admin'
        return 'unknown'

    # [Authorize] attribute with roles
    auth_match = _AUTHORIZE.search(cb)
    if auth_match:
        role_m = _AUTH_ROLE.search(auth_match.group(1))
        if role_m:
            return f'role:{role_m.group(1)}'
        return 'authenticated'

    # User.IsInRole("...")
    roles = _IS_IN_ROLE.findall(cb)
    if roles:
        return f'role:{",".join(dict.fromkeys(roles))}'

    # Request.IsAuthenticated
    if _IS_AUTH.search(cb):
        return 'authenticated'

    # Admin folder heuristic
    if 'admin' in folder_low:
        return 'role:Admin'

    return 'unknown'


# ---------------------------------------------------------------------------
# Public parsers
# ---------------------------------------------------------------------------

def parse_aspx_page(record: dict) -> dict:
    """Parse .aspx + code-behind into structured metadata. Does NOT include raw content."""
    content = record.get('content', '')
    cb      = record.get('codebehind_content', '')
    rel     = record.get('rel_path', '')
    folder  = str(Path(rel).parent) if rel else ''
    if folder == '.':
        folder = ''

    result: Dict[str, Any] = {
        'name':                record.get('name', ''),
        'filename':            record.get('filename', ''),
        'path':                record.get('path', ''),
        'rel_path':            rel,
        'folder':              folder,
        'title':               '',
        'master_page':         '',
        'codebehind_file':     '',
        'inherits':            '',
        'namespace':           '',
        'class_name':          '',
        'base_class':          '',
        'controls_registered': [],
        'form_controls':       [],
        'display_controls':    [],
        'data_sources':        [],
        'content_areas':       [],
        'content_placeholders':[],
        'navigation_links':    [],
        'navigation_out':      [],
        'event_handlers':      [],
        'imports':             [],
        'uses_ajax':           False,
        'uses_sql_direct':     False,
        'has_login_controls':  False,
        'page_load':           False,
        'auth':                'unknown',
        'functional_area':     '',
        'purpose':             '',
    }

    # ---- Directives ----
    m = _PAGE_DIR.search(content)
    if m:
        attrs = _parse_attrs(m.group(1))
        result['title']          = attrs.get('title', '')
        result['master_page']    = attrs.get('masterpagefile', '').replace('~/', '').lstrip('/')
        result['codebehind_file']= attrs.get('codebehind', attrs.get('codefile', ''))
        result['inherits']       = attrs.get('inherits', '')

    for m in _REGISTER_DIR.finditer(content):
        attrs = _parse_attrs(m.group(1))
        src   = attrs.get('src', '').replace('~/', '').lstrip('/')
        if src:
            result['controls_registered'].append({
                'src':    src,
                'tag':    attrs.get('tagname', ''),
                'prefix': attrs.get('tagprefix', 'uc'),
            })

    # ---- Server controls ----
    ctrl_types: set = set()
    for m in _ASPNET_TAG.finditer(content):
        ctype    = m.group(1).lower()
        attr_str = m.group(2)
        cid      = _ID_ATTR.search(attr_str)
        ctxt     = _TEXT_ATTR.search(attr_str)
        nav_url  = _NAV_URL.search(attr_str)

        ctrl_info = {
            'type': ctype,
            'id':   cid.group(1) if cid else '',
            'text': ctxt.group(1) if ctxt else '',
        }

        if ctype in _FORM_CTRL_TYPES:
            result['form_controls'].append(ctrl_info)
            ctrl_types.add(ctype)
        elif ctype in _DISPLAY_CTRL_TYPES:
            result['display_controls'].append(ctrl_info)
        elif ctype in _DATA_SRC_TYPES:
            result['data_sources'].append(ctrl_info)
        elif ctype in _AJAX_TYPES:
            result['uses_ajax'] = True
        elif ctype in _LOGIN_TYPES:
            result['has_login_controls'] = True
        elif ctype == 'hyperlink' and nav_url:
            url_val  = nav_url.group(1) or nav_url.group(2) or ''
            route_m  = _ROUTE_URL.search(url_val)
            nav_entry: Dict[str, Any] = {
                'type': 'route' if route_m else 'hyperlink',
                'url':  url_val,
                'text': ctrl_info['text'],
            }
            if route_m:
                nav_entry['route_name'] = route_m.group(1)
            result['navigation_links'].append(nav_entry)
        elif ctype == 'content':
            pass  # handled below
        elif ctype in _NAV_CTRL_TYPES:
            pass  # just noted

    result['content_areas']        = _CONTENT_AREA.findall(content)
    result['content_placeholders'] = _CONTENT_PH.findall(content)

    # NavigateUrl route expressions — full-content scan bypasses asp-tag > truncation
    for rm in _NAVURL_ROUTE.finditer(content):
        url_val = rm.group(1) or rm.group(2) or ''
        rte_m = _ROUTE_URL.search(url_val)
        if rte_m:
            result['navigation_links'].append({
                'type':       'route',
                'url':        url_val,
                'text':       '',
                'route_name': rte_m.group(1),
            })

    # HTML anchors — also capture route expressions embedded in href values
    for href in _ANCHOR_HREF.findall(content):
        href = href.strip()
        if href and not href.startswith(('#', 'javascript:', 'mailto:')):
            route_m = _ROUTE_URL.search(href)
            entry: Dict[str, Any] = {
                'type': 'route' if route_m else 'anchor',
                'url':  href,
                'text': '',
            }
            if route_m:
                entry['route_name'] = route_m.group(1)
            result['navigation_links'].append(entry)

    # ---- Code-behind ----
    if cb:
        ns_m = _NAMESPACE.search(cb)
        if ns_m:
            result['namespace'] = ns_m.group(1)

        cls_m = _CLASS_DECL.search(cb)
        if cls_m:
            result['class_name'] = cls_m.group(1)
            result['base_class'] = cls_m.group(2) or ''

        result['imports']      = list(dict.fromkeys(_USING.findall(cb)))
        result['page_load']    = bool(_PAGE_LOAD.search(cb))

        for ctrl_name, event_type in _EVENT_HANDLER.findall(cb):
            result['event_handlers'].append(f"{ctrl_name}_{event_type}")

        for url in _REDIRECT.findall(cb):
            result['navigation_out'].append({'type': 'redirect', 'url': url})
        for url in _TRANSFER.findall(cb):
            result['navigation_out'].append({'type': 'transfer', 'url': url})

        result['uses_sql_direct'] = bool(_SQL_DIRECT.search(cb))

    has_grid = any(t in ctrl_types for t in {'gridview', 'listview', 'repeater',
                                              'datalist', 'datagrid', 'detailsview'})
    has_form = any(t in ctrl_types for t in {'textbox', 'dropdownlist', 'listbox',
                                              'checkbox', 'radiobutton', 'fileupload'})

    result['functional_area'] = _infer_functional_area(
        result['name'], result['folder'], result['imports']
    )
    result['purpose'] = _infer_page_purpose(
        result['name'], result['folder'], ctrl_types, has_grid, has_form,
        result['imports']
    )
    result['auth'] = _infer_auth(result['name'], result['folder'], cb)

    return result


def parse_ascx_control(record: dict) -> dict:
    """Parse .ascx user control into structured metadata."""
    content = record.get('content', '')
    cb      = record.get('codebehind_content', '')
    rel     = record.get('rel_path', '')

    result: Dict[str, Any] = {
        'name':          record.get('name', ''),
        'filename':      record.get('filename', ''),
        'path':          record.get('path', ''),
        'rel_path':      rel,
        'folder':        str(Path(rel).parent) if rel else '',
        'inherits':      '',
        'class_name':    '',
        'namespace':     '',
        'form_controls': [],
        'event_handlers':[],
        'properties':    [],
        'used_by_pages': [],
        'purpose':       '',
    }

    m = _PAGE_DIR.search(content)
    if m:
        result['inherits'] = _parse_attrs(m.group(1)).get('inherits', '')

    for m in _ASPNET_TAG.finditer(content):
        ctype = m.group(1).lower()
        cid_m = _ID_ATTR.search(m.group(2))
        result['form_controls'].append({
            'type': ctype,
            'id':   cid_m.group(1) if cid_m else '',
        })

    if cb:
        ns_m = _NAMESPACE.search(cb)
        if ns_m:
            result['namespace'] = ns_m.group(1)
        cls_m = _CLASS_DECL.search(cb)
        if cls_m:
            result['class_name'] = cls_m.group(1)
        for ctrl_name, evt in _EVENT_HANDLER.findall(cb):
            result['event_handlers'].append(f"{ctrl_name}_{evt}")
        result['properties'] = re.findall(
            r'public\s+\w[\w<>[\]]*\s+(\w+)\s*\{[^}]*get\s*;', cb
        )

    name = result['name'].lower()
    if 'header' in name:
        result['purpose'] = 'Page header / top navigation component'
    elif 'footer' in name:
        result['purpose'] = 'Page footer component'
    elif 'menu' in name or 'nav' in name:
        result['purpose'] = 'Navigation menu component'
    elif 'login' in name:
        result['purpose'] = 'Login widget component'
    elif 'search' in name:
        result['purpose'] = 'Search input component'
    elif 'sidebar' in name:
        result['purpose'] = 'Sidebar / side panel component'
    elif 'breadcrumb' in name or 'crumb' in name:
        result['purpose'] = 'Breadcrumb navigation component'
    elif 'pager' in name or 'pagination' in name:
        result['purpose'] = 'Pagination control component'
    elif 'toolbar' in name:
        result['purpose'] = 'Toolbar / action bar component'
    else:
        result['purpose'] = f'{result["name"]} reusable UI component'

    return result


def parse_master_page(record: dict) -> dict:
    """Parse .master page into structured metadata."""
    content = record.get('content', '')
    cb      = record.get('codebehind_content', '')

    result: Dict[str, Any] = {
        'name':                 record.get('name', ''),
        'filename':             record.get('filename', ''),
        'path':                 record.get('path', ''),
        'rel_path':             record.get('rel_path', ''),
        'class_name':           '',
        'namespace':            '',
        'content_placeholders': _CONTENT_PH.findall(content),
        'controls_registered':  [],
        'used_by_pages':        [],
        'navigation_menus':     [],
        'has_login_controls':   False,
        'uses_ajax':            False,
        'purpose':              'Layout master template',
    }

    for m in _REGISTER_DIR.finditer(content):
        attrs = _parse_attrs(m.group(1))
        src   = attrs.get('src', '').replace('~/', '').lstrip('/')
        if src:
            result['controls_registered'].append({
                'src':    src,
                'prefix': attrs.get('tagprefix', ''),
            })

    for m in _ASPNET_TAG.finditer(content):
        ctype = m.group(1).lower()
        if ctype in _LOGIN_TYPES:
            result['has_login_controls'] = True
        elif ctype in _NAV_CTRL_TYPES:
            result['navigation_menus'].append(f'asp:{m.group(1)}')
        elif ctype in _AJAX_TYPES:
            result['uses_ajax'] = True

    if cb:
        ns_m = _NAMESPACE.search(cb)
        if ns_m:
            result['namespace'] = ns_m.group(1)
        cls_m = _CLASS_DECL.search(cb)
        if cls_m:
            result['class_name'] = cls_m.group(1)

    # Name-based purpose refinement
    name_low = result['name'].lower()
    if 'admin' in name_low:
        result['purpose'] = 'Admin area layout template'
    elif 'print' in name_low:
        result['purpose'] = 'Print layout template'
    elif 'mobile' in name_low:
        result['purpose'] = 'Mobile layout template'
    elif 'empty' in name_low or 'blank' in name_low:
        result['purpose'] = 'Minimal / blank layout template'

    return result


def parse_web_config(record: dict) -> dict:
    """Extract auth and connection info from web.config."""
    content = record.get('content', '')

    result: Dict[str, Any] = {
        'auth_mode':          '',
        'forms_auth_url':     '',
        'connection_strings': [],
        'roles':              [],
        'location_rules':     [],
        'custom_errors_mode': '',
        'session_mode':       '',
        'smtp_host':          '',
    }

    # Auth mode
    m = re.search(r'<authentication\s+mode\s*=\s*"([^"]+)"', content, re.IGNORECASE)
    if m:
        result['auth_mode'] = m.group(1)

    # Forms login URL
    m = re.search(r'<forms\b[^>]*loginUrl\s*=\s*"([^"]+)"', content, re.IGNORECASE)
    if m:
        result['forms_auth_url'] = m.group(1)

    # Connection string names
    result['connection_strings'] = re.findall(
        r'<add\s+name\s*=\s*"([^"]+)"[^>]*connectionString', content, re.IGNORECASE
    )

    # Custom errors
    m = re.search(r'<customErrors\s+mode\s*=\s*"([^"]+)"', content, re.IGNORECASE)
    if m:
        result['custom_errors_mode'] = m.group(1)

    # Session mode
    m = re.search(r'<sessionState\s+mode\s*=\s*"([^"]+)"', content, re.IGNORECASE)
    if m:
        result['session_mode'] = m.group(1)

    # SMTP — host may sit on <smtp> or on the nested <network> element
    m = (re.search(r'<smtp\b[^>]*host\s*=\s*"([^"]+)"', content, re.IGNORECASE)
         or re.search(r'<network\b[^>]*host\s*=\s*"([^"]+)"', content, re.IGNORECASE))
    if m:
        result['smtp_host'] = m.group(1)

    # Location access rules
    for path_m in re.finditer(
        r'<location\s+path\s*=\s*"([^"]+)"[^>]*>(.*?)</location>',
        content, re.DOTALL | re.IGNORECASE
    ):
        loc_body = path_m.group(2)
        allow    = re.findall(r'<allow\s+([^/]+)/>', loc_body, re.IGNORECASE)
        deny     = re.findall(r'<deny\s+([^/]+)/>', loc_body, re.IGNORECASE)
        result['location_rules'].append({
            'path':  path_m.group(1),
            'allow': [a.strip() for a in allow],
            'deny':  [d.strip() for d in deny],
        })

    return result
