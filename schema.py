from models import (
    Todo as TodoModel,
    session
)
import graphene
from graphene_sqlalchemy import (
    SQLAlchemyConnectionField,
    SQLAlchemyObjectType
)
from flask_bcrypt import Bcrypt
from typing import Optional
from graphene_file_upload.scalars import Upload
from helpers import file_path
import os
# types



class Todos(SQLAlchemyObjectType):
    class Meta:
        model = TodoModel

class addTodo(graphene.Mutation):
    class Arguments:
        title = graphene.String()
        description = graphene.String()
        file1 = Upload()
    ok = graphene.Boolean()
    todo = graphene.Field(Todos)

    # def mutate(root, info, title, description,file1):
    def mutate(root, info,title,description, file1):    
        # find user based on token payload
        filename = file1.filename
        file1.save(os.path.join(file_path,filename))
        todo_record = TodoModel(
            title=title,
            description=description,
            path=filename
        )
        session.add(todo_record)
        session.commit()
        ok = True
        # return addTodo(ok=ok, todo=todo_record)
        return addTodo(ok=ok)
class updateTodo(graphene.Mutation):
    class Arguments:
        todo_id = graphene.Int()
        title = graphene.String()
        description = graphene.String()
        path = Upload()
    ok = graphene.Boolean()
    todo = graphene.Field(Todos)

    def mutate(root, info, todo_id, title: Optional[str]=None, description: Optional[str]=None,file1:Optional[Upload]=None):
        # find note object
        todo = session.query(TodoModel).filter_by(id=todo_id).first()
        todo.title = title
        todo.description = description
        filename = file1.filename
        file1.save(os.path.join(file_path,filename))
        session.commit()
        ok = True
        todo = todo
        return updateTodo(ok=ok, todo=todo)
    
class deleteTodo(graphene.Mutation):
    class Arguments:
        todo_id = graphene.Int()
    ok = graphene.Boolean()
    todo = graphene.Field(Todos)

    def mutate(root, info, todo_id):
        todo = session.query(TodoModel).filter_by(id=todo_id).first()
        session.delete(todo)
        ok = True
        todo = todo
        session.commit()
        return deleteTodo(ok=ok, todo=todo)
    
class Mutation(graphene.ObjectType):
    add_todo = addTodo.Field()
    update_todo = updateTodo.Field()
    delete_todo = deleteTodo.Field()

class Query(graphene.ObjectType):
    # find single note
    findTodo = graphene.Field(Todos, id=graphene.Int())
    # get all notes by user
    user_notes = graphene.List(Todos)

    def resolve_findTodo(root, info, id):
        return session.query(TodoModel).filter_by(id=id).first()
    def resolve_user_notes(root, info,):
        return session.query(TodoModel).all()

# class Query(graphene.ObjectType):
#     ok = graphene.Boolean(default_value=True)

# class MyUpload(graphene.Mutation):
#     class Arguments:
#         file_in = Upload()

#     ok = graphene.Boolean()

#     def mutate(self, info, file_in):
#         for line in file_in:
#             print(line)
#         return MyUpload(ok=True)

# class Mutation(graphene.ObjectType):
#     my_upload = MyUpload.Field()





# schema = graphene.Schema(query=Query, mutation=Mutation)
schema = graphene.Schema(query=Query, mutation=Mutation)
               