from db import db

class Messages(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(80), unique=True, nullable=False)
    
    def __repr__(self):
        return f'<Message {self.message}>'