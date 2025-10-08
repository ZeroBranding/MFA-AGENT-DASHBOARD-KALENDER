#!/usr/bin/env python3
"""Load test: send 100 synthetic emails to agent."""
import threading, random, string, time, shutil, os, sqlite3, asyncio
from datetime import datetime
from unified_agent_coordinator import UnifiedAgentCoordinator
from calendar_integration import CalendarIntegration
from app.calendar.db import get_calendar_db

TEST_DB = "calendar_test_load.db"

# copy db
if os.path.exists(TEST_DB):
    os.remove(TEST_DB)
shutil.copy('calendar.db', TEST_DB)

# patch calendar db to use test db
get_calendar_db(TEST_DB)

coordinator = UnifiedAgentCoordinator()
coordinator.calendar_integration.scheduler.db = get_calendar_db(TEST_DB)
coordinator.calendar_integration.booker.db = get_calendar_db(TEST_DB)
coordinator.calendar_integration.canceller.db = get_calendar_db(TEST_DB)

lock = threading.Lock()
results = []

def random_email(i):
    sender = f"user{i}@example.com"
    subject = random.choice(["Termin", "Bestätigung", "Absage"])
    body = "Hallo, ich " + random.choice([
        "hätte gerne einen Termin.",
        "nehme Termin 1.",
        "muss meinen Termin absagen."])    
    email = {
        'subject': subject,
        'body': body,
        'sender': sender,
        'sender_name': f"User {i}",
        'message_id': f"msg{i}",
        'thread_id': f"thread{i}"
    }
    return email

def worker(batch):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    for e in batch:
        resp = loop.run_until_complete(coordinator.process_email_unified(e))
        with lock:
            results.append(resp)
    loop.close()

emails = [random_email(i) for i in range(100)]
chunk = 100//8
threads = []
start=time.time()
for t in range(8):
    batch = emails[t*chunk:(t+1)*chunk]
    th = threading.Thread(target=worker,args=(batch,))
    th.start()
    threads.append(th)
for th in threads:
    th.join()
end=time.time()
print("Processed", len(results), "emails in", round(end-start,2),"s")
confirms=sum(1 for r in results if r.intent_detected)
print("With intents:", confirms)
# cleanup
os.remove(TEST_DB)
