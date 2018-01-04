# coding: utf-8
from collections import OrderedDict

from sqlalchemy import Column, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

db_types = [
    'postgresql', 'mysql', 'oracle', 'sqlite', 'firebird', 'mssql',
    'default',  # don't move it
]
Base = declarative_base()
existing = {}
m2m_models = {}


def declare(model_info, db=None, back_type=None):
    table_name = model_info['name']
    if table_name in existing:
        return existing[table_name]

    row_kwargs = OrderedDict({'__tablename__': table_name})
    for name, field in model_info['fields'].items():
        col_types = {
            (db_type if db_type + '_type' in field else 'default'): field.pop(db_type + '_type', {})
            for db_type in db_types
        }
        col_type_options = {
            (db_type if db_type + '_type_option' in field else 'default'): field.pop(db_type + '_type_option', {})
            for db_type in db_types
        }
        type_key = db if db in col_types else 'default'
        col_type = col_types.get(type_key)
        col_type_option = col_type_options.get(type_key, {})

        rel_option = field.pop('rel_option', None)
        if col_type:
            col_args = [col_type(**col_type_option)]
            if 'fk_option' in field:
                col_args.append(ForeignKey(**field.pop('fk_option', {})))

            row_kwargs[name] = Column(*col_args, **field)

        if rel_option:
            if 'secondary' in rel_option:
                from . import copy
                m2m_models[rel_option['secondary']._meta.object_name] = model = copy(rel_option['secondary'])
                rel_option['secondary'] = model
            
            if 'logical_name' in rel_option:
                name = rel_option.pop('logical_name')

            back = rel_option.pop('back', None)
            if back and back_type:
                rel_option[back_type] = back

            row_kwargs[name] = relationship(rel_option.pop('target'), **rel_option)

    cls = existing[table_name] = type(table_name, (Base,), row_kwargs)
    return cls

