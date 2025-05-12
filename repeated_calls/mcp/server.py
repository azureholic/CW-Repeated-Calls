import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from mcp.server.fastmcp import Context, FastMCP
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from repeated_calls.database import tables


@dataclass
class AppContext:
    engine: Engine


@asynccontextmanager
async def lifespan(app: FastMCP) -> AsyncIterator[AppContext]:
    """Lifespan context manager for the MCP server."""
    from repeated_calls.database import engine

    try:
        yield AppContext(engine=engine)
    finally:
        pass


mcp = FastMCP("Repeated Calls Database", lifespan=lifespan)


@mcp.tool()
def get_call_events(customer_id: str, ctx: Context) -> str:
    """Get all call events from for a specific customer."""
    engine = ctx.request_context.lifespan_context.engine

    with Session(engine) as session:
        q = (
            select(tables.HistoricCallEvent)
            .where(tables.HistoricCallEvent.customer_id == customer_id)
            .order_by(tables.HistoricCallEvent.start_time.desc())
        )
        res = session.execute(q).all()

    data = [row._asdict() for row in res]
    return json.dumps(data)


if __name__ == "__main__":
    mcp.run(transport="sse")
