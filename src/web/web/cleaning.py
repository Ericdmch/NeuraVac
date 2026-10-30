"""Roomba 600 Open Interface cleaning motor commands."""


def cleaning_command(vacuum, side_brush, main_brush):
    if any(type(value) is not bool for value in (vacuum, side_brush, main_brush)):
        raise ValueError('All motor states must be boolean')
    return [138, (2 if vacuum else 0) | (1 if side_brush else 0) | (4 if main_brush else 0)]
