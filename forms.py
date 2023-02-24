from flask_wtf import FlaskForm
from wtforms import (StringField, TextAreaField, IntegerField, BooleanField,
                     RadioField,FileField)
                     
from wtforms.validators import InputRequired, Length

class TodoForm(FlaskForm):
    title = StringField('Title', validators=[InputRequired()])
    description = TextAreaField('Course Description',
                                validators=[InputRequired(),
                                            Length(max=200)])
    file1 = FileField()
    
    
