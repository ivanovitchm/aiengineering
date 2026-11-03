from typing import Literal
import pandas as pd
from fastmcp import FastMCP                                   # ←

cars = pd.read_csv("cars.csv")
mcp = FastMCP("estoque-natal")                                # ← o servidor, com um nome

# ─── TOOLS: o modelo decide quando chamar ───

@mcp.tool                                                     # ← isto substitui o JSON Schema escrito à mão
def search_cars(max_price: float, body: Literal["SUV", "sedan", "hatch"] | None = None) -> dict:
    """Search the used-car stock by budget and body type.
    Returns how many cars matched and the 5 newest ones (car_id, model, year, km, price)."""
    r = cars[cars.price_brl <= max_price]
    if body is not None:
        r = r[r.body == body]
    r = r.sort_values(["year", "km"], ascending=[False, True])
    cols = ["car_id", "brand", "model", "year", "km", "price_brl", "transmission"]
    return {"total_found": len(r), "cars": r[cols].head(5).to_dict("records")}

@mcp.tool                                                     # ←
def car_details(car_id: str) -> dict:
    """Get all the details of one car: trunk size (liters), fuel consumption (km/l),
    color and city. Use it with a car_id returned by search_cars."""
    r = cars[cars.car_id == car_id]
    if r.empty:
        return {"error": f"no car with id {car_id}"}
    return r.to_dict("records")[0]

@mcp.tool                                                     # ←
def compare_cars(car_ids: list[str]) -> dict:
    """Compare 2 to 4 cars side by side (year, km, price, transmission, trunk size, consumption).
    Use it when the user wants to choose between specific cars."""
    r = cars[cars.car_id.isin(car_ids)]
    if r.empty:
        return {"error": f"none of these ids exist: {car_ids}"}
    cols = ["car_id", "brand", "model", "year", "km", "price_brl", "transmission", "trunk_l", "consumption_kml"]
    def winners(col, highest):
        target = r[col].max() if highest else r[col].min()
        return list(r[r[col] == target].car_id)              # mais de um id = empate
    best = {"largest_trunk": winners("trunk_l", True),
            "most_economical": winners("consumption_kml", True),   # mais km por litro = consome menos
            "cheapest": winners("price_brl", False),
            "newest": winners("year", True),
            "lowest_km": winners("km", False)}
    return {"cars": r[cols].to_dict("records"), "best": best,
            "missing": [i for i in car_ids if i not in set(r.car_id)]}


# ─── RESOURCE: a aplicação lê, por um endereço ───

@mcp.resource("estoque://schema")                             # ←
def schema() -> str:
    """The columns of the stock table."""
    return ", ".join(cars.columns)


# ─── PROMPT: o usuário escolhe usar ───

@mcp.prompt                                                   # ←
def recomendar(orcamento: int, carroceria: str) -> str:
    """Ask for a recommendation with budget and body type filled in."""
    return f"Quero um {carroceria} até R$ {orcamento}. Busque no estoque e recomende 3 carros, citando o car_id."


if __name__ == "__main__":
    mcp.run()                                                 # ← fala MCP pelo stdio (entrada e saída padrão)
