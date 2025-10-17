# === RECONNECT HELPER (no global conflict) ===
async def rebuild_session_service():
    """
    Rebuilds the DatabaseSessionService safely.
    Keeps the same logical session metadata and Kerberos cache.
    """
    print("Rebuilding DatabaseSessionService (same session)...")

    try:
        if hasattr(session_service, "engine") and session_service.engine:
            await asyncio.to_thread(session_service.engine.dispose)
            print("Old Oracle connection pool disposed.")

        new_service = DatabaseSessionService(
            db_url=db_url,
            connect_args={
                "host": host,
                "port": port,
                "service_name": service_name
            },
            pool_args=pool_args
        )

        print("Reconnected successfully. Same SESSION_ID reused.")
        return new_service

    except Exception as e:
        print(f"Reconnect failed: {e}")
        raise


# === SAFE WRAPPER TO HANDLE IDLE TIMEOUT RECONNECT ===
async def run_with_reconnect(query, session_service=session_service):
    try:
        return await main(query, session_service)

    except oracledb.Error as e:
        if "ORA-03113" in str(e) or "DPI-1080" in str(e):
            print("Oracle connection lost (idle timeout). Attempting reconnect...")

            # rebuild and reassign locally, not globally
            new_service = await rebuild_session_service()
            return await main(query, new_service)

        else:
            raise