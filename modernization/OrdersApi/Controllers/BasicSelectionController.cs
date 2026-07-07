using Microsoft.AspNetCore.Mvc;
using OrdersApi.Data;
using OrdersApi.Models;

namespace OrdersApi.Controllers;

[ApiController]
[Route("api/basic-selection-orders")]
public class BasicSelectionController : ControllerBase
{
    // GET /api/basic-selection-orders
    [HttpGet]
    public ActionResult<IEnumerable<Order>> GetAll()
    {
        return Ok(BasicSelectionOrdersRepository.GetAll());
    }
}
