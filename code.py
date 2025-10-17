async def run_with_reconnect(query, session_service=session_service):
    try:
        return await main(query, session_service)

    except oracledb.Error as e:
        if "ORA-03113" in str(e) or "DPI-1080" in str(e):
            print("Oracle connection lost (idle timeout). Attempting reconnect...")

            try:
                # Dispose of the old connection pool if it exists
                if hasattr(session_service, "engine") and session_service.engine:
                    await asyncio.to_thread(session_service.engine.dispose)
                    print("Old Oracle connection pool disposed.")

                # Rebuild DatabaseSessionService with same configuration
                global session_service
                session_service = DatabaseSessionService(
                    db_url=db_url,
                    connect_args={
                        "host": host,
                        "port": port,
                        "service_name": service_name
                    },
                    pool_args=pool_args
                )

                print("Reconnected successfully. Same SESSION_ID reused.")
                return await main(query, session_service)

            except Exception as inner:
                print(f"Reconnect failed: {inner}")
                raise

        else:
            raise


# === OPTIONAL KEEP-ALIVE TASK ===
async def keepalive():
    while True:
        try:
            await session_service.run("SELECT 1 FROM DUAL")
        except Exception as e:
            print(f"[KeepAlive Warning] {e}")
        await asyncio.sleep(1200)  # every 20 minutes
        
        
        


==========================


from fastapi import FastAPI
import asyncio
from agents.smartassist import run_with_reconnect, session_service

app = FastAPI()

# ✅ Start keepalive when app launches
@app.on_event("startup")
async def start_keepalive():
    asyncio.create_task(keepalive())   # background task
    print("Keepalive task started")


@app.post("/smartassist")
async def smartassist_endpoint(query: str):
    try:
        # use run_with_reconnect wrapper
        answer = await run_with_reconnect(query, session_service)
        return {"result": answer}
    except Exception as e:
        print(f"Error in smartassist: {e}")
        return {"error": str(e)}
        