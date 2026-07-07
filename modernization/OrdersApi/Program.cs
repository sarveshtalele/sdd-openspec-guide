var builder = WebApplication.CreateBuilder(args);

builder.Services.AddControllers();

// The Vite dev server (default http://localhost:5173) is a different origin
// than this API, so the browser blocks fetches without an explicit CORS
// policy allowing it. See openspec/changes/modernize-grid-checkbox-selection/design.md.
const string DevFrontendPolicy = "DevFrontend";
builder.Services.AddCors(options =>
{
    options.AddPolicy(DevFrontendPolicy, policy =>
    {
        policy.WithOrigins("http://localhost:5173")
              .AllowAnyHeader()
              .AllowAnyMethod();
    });
});

var app = builder.Build();

app.UseCors(DevFrontendPolicy);
app.MapControllers();

app.Run();
