from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse

from sqlalchemy import Column, Integer, String, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from datetime import datetime, timezone
import csv
import io
import os

# ================= DATABASE =================

DATABASE_URL = "sqlite:///./complaint.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# ================= APP =================

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

if not os.path.exists("uploads"):
    os.makedirs("uploads")

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# ================= CORS =================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================= ROUND ROBIN TRACKER =================

assignment_tracker = {
    "hostel staff": 0,
    "academic staff": 0,
    "infrastructure staff": 0,
    "administrative staff": 0
}

# ================= MODELS =================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    password = Column(String)
    role = Column(String)


class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True)
    title = Column(String)
    description = Column(String)

    category = Column(String)
    sub_category = Column(String)
    priority = Column(String)

    status = Column(String, default="Open")

    user_id = Column(Integer)
    assigned_to = Column(Integer, nullable=True)

    file_path = Column(String, nullable=True)
    comment = Column(String, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

Base.metadata.create_all(bind=engine)
# ================= CHAT MODEL =================
class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True)
    complaint_id = Column(Integer)
    user_id = Column(Integer)
    message = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


# ================= NOTIFICATION MODEL =================
class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    message = Column(String)
    is_read = Column(String, default="no")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

# ✅ ✅ PUT IT HERE (AFTER ALL MODELS)
Base.metadata.create_all(bind=engine)
# ================= DB =================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ================= REGISTER =================

@app.post("/register")
def register(data: dict, db: Session = Depends(get_db)):

    existing_user = db.query(User).filter(User.username == data["username"]).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    user = User(
        username=data["username"],
        password=data["password"],
        role=data["role"]
    )

    db.add(user)
    db.commit()

    return {"message": "User registered"}

# ================= LOGIN =================

@app.post("/login")
def login(data: dict, db: Session = Depends(get_db)):

    user = db.query(User).filter(
        User.username == data["username"],
        User.password == data["password"],
        User.role == data["role"]
    ).first()

    if not user:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    return {"id": user.id, "username": user.username, "role": user.role}

# ================= UPLOAD =================

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):

    file_location = f"uploads/{file.filename}"

    with open(file_location, "wb") as f:
        f.write(await file.read())

    return {"file_path": file_location}

# ================= CREATE COMPLAINT (ROUND ROBIN AUTO ASSIGN) =================

@app.post("/create-complaint")
def create_complaint(data: dict, db: Session = Depends(get_db)):

    print("🔥 RECEIVED:", data)

    category = data.get("category")

    staff_map = {
        "Hostel": "hostel staff",
        "Academic": "academic staff",
        "Infrastructure": "infrastructure staff",
        "Administrative": "administrative staff"
    }

    assigned_staff = None

    if category in staff_map:
        staff_role = staff_map[category]

        staff_users = db.query(User).filter(User.role == staff_role).all()

        if staff_users:
            index = assignment_tracker[staff_role] % len(staff_users)
            assigned_staff = staff_users[index].id
            assignment_tracker[staff_role] += 1
    # 🔔 NOTIFICATION FOR STAFF
    if assigned_staff:
      db.add(Notification(
          user_id=assigned_staff,
          message=f"New complaint assigned: {data.get('title')}"
       ))        

    complaint = Complaint(
        title=data.get("title"),
        description=data.get("description"),
        category=category,
        sub_category=data.get("sub_category"),
        priority=data.get("priority"),
        user_id=int(data.get("user_id")),
        assigned_to=assigned_staff,
        status="Assigned" if assigned_staff else "Open",
        file_path=data.get("file_path")
    )

    db.add(complaint)
    db.commit()
    db.refresh(complaint)

    print("✅ SAVED:", complaint.id)

    return {"message": "Complaint created"}
# ================= ADD MESSAGE =================
@app.post("/add-message")
def add_message(data: dict, db: Session = Depends(get_db)):

    msg = Comment(
        complaint_id=data["complaint_id"],
        user_id=data["user_id"],
        message=data["message"]
    )

    db.add(msg)

    # 🔔 NOTIFICATION to complaint owner
    complaint = db.query(Complaint).filter(
        Complaint.id == data["complaint_id"]
    ).first()

    if complaint:
        db.add(Notification(
            user_id=complaint.user_id,
            message="New reply on your complaint"
        ))

    db.commit()

    return {"message": "Message added"}


# ================= GET MESSAGES =================
@app.get("/get-messages/{complaint_id}")
def get_messages(complaint_id: int, db: Session = Depends(get_db)):

    return db.query(Comment).filter(
        Comment.complaint_id == complaint_id
    ).all()
# ================= GET NOTIFICATIONS =================
@app.get("/notifications/{user_id}")
def get_notifications(user_id: int, db: Session = Depends(get_db)):
    return db.query(Notification).filter(Notification.user_id == user_id).all()
# ================= GET =================

@app.get("/all-complaints")
def get_all(db: Session = Depends(get_db)):
    return db.query(Complaint).all()

@app.get("/user-complaints/{user_id}")
def user_complaints(user_id: int, db: Session = Depends(get_db)):
    return db.query(Complaint).filter(Complaint.user_id == user_id).all()

@app.get("/staff-complaints/{staff_id}")
def staff_complaints(staff_id: int, db: Session = Depends(get_db)):
    return db.query(Complaint).filter(
        Complaint.assigned_to == int(staff_id),
        Complaint.status != "Closed"
    ).all()

# ================= ASSIGN =================

@app.put("/assign-complaint/{complaint_id}")
def assign(complaint_id: int, data: dict, db: Session = Depends(get_db)):

    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()

    if not complaint:
        raise HTTPException(status_code=404, detail="Not found")

    complaint.assigned_to = int(data["staff_id"])
    complaint.status = "Assigned"
    complaint.updated_at = datetime.now(timezone.utc)

    db.commit()

    return {"message": "Assigned successfully"}

# ================= UPDATE =================

@app.put("/update-status/{complaint_id}")
def update_status(complaint_id: int, data: dict, db: Session = Depends(get_db)):

    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()

    complaint.status = data["status"]
    # 🔔 NOTIFICATION FOR USER
    if data["status"] == "Resolved":
       db.add(Notification(
          user_id=complaint.user_id,
          message="Your complaint has been resolved"
        ))
    complaint.updated_at = datetime.now(timezone.utc)

    db.commit()

    return {"message": "Updated"}

# ================= COMMENT =================

@app.put("/add-comment/{complaint_id}")
def add_comment(complaint_id: int, data: dict, db: Session = Depends(get_db)):

    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()

    if not complaint:
        raise HTTPException(status_code=404, detail="Not found")

    complaint.comment = data["comment"]
    complaint.updated_at = datetime.now(timezone.utc)

    db.commit()

    return {"message": "Comment added"}

# ================= STAFF =================

@app.get("/all-staff")
def get_staff(db: Session = Depends(get_db)):
    return db.query(User).filter(
        User.role.in_([
            "academic staff",
            "hostel staff",
            "infrastructure staff",
            "administrative staff"
        ])
    ).all()

# ================= CSV =================

def generate_csv(complaints):
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["ID", "Title", "Description", "Category", "Priority", "Status"])

    for c in complaints:
        writer.writerow([c.id, c.title, c.description, c.category, c.priority, c.status])

    output.seek(0)
    return output

@app.get("/download-all")
def download_all(db: Session = Depends(get_db)):
    return StreamingResponse(
        generate_csv(db.query(Complaint).all()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=all.csv"}
    )

@app.get("/download-user/{user_id}")
def download_user(user_id: int, db: Session = Depends(get_db)):
    return StreamingResponse(
        generate_csv(db.query(Complaint).filter(Complaint.user_id == user_id).all()),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=user_{user_id}.csv"}
    )

@app.get("/download-staff/{staff_id}")
def download_staff(staff_id: int, db: Session = Depends(get_db)):
    return StreamingResponse(
        generate_csv(db.query(Complaint).filter(Complaint.assigned_to == int(staff_id)).all()),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=staff_{staff_id}.csv"}
    )

# ================= FILTER =================

@app.get("/filter-complaints")
def filter_complaints(status: str = None, category: str = None, db: Session = Depends(get_db)):
    query = db.query(Complaint)

    if status:
        query = query.filter(Complaint.status == status)

    if category:
        query = query.filter(Complaint.category == category)

    return query.all()

# ================= ADMIN STATS =================

@app.get("/admin-stats")
def admin_stats(db: Session = Depends(get_db)):
    total = db.query(Complaint).count()
    resolved = db.query(Complaint).filter(Complaint.status == "Resolved").count()
    pending = db.query(Complaint).filter(Complaint.status != "Resolved").count()

    return {
        "total": total,
        "resolved": resolved,
        "pending": pending
    }