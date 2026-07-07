using Microsoft.AspNetCore.Mvc;
using OrdersApi.Data;
using OrdersApi.Models;

namespace OrdersApi.Controllers;

[ApiController]
[Route("api/checkbox-selection-orders")]
public class CheckboxSelectionController : ControllerBase
{
    // GET /api/checkbox-selection-orders
    [HttpGet]
    public ActionResult<IEnumerable<Order>> GetAll()
    {
        return Ok(CheckboxSelectionOrdersRepository.GetAll());
    }
}
