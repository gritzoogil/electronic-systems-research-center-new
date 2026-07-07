from app import db


def reorder_on_create(model, requested_order, filters=None):
    """Before inserting a new row at `requested_order`, shift every existing
    row at or after that position down by 1, so nothing collides.
    If `requested_order` is beyond the current count, clamp it to
    'next available slot' instead of leaving gaps.
    `filters` is an optional dict of extra WHERE conditions (e.g. scoping
    Resource pages to one parent resource, or Partner order within a category).
    Returns the final, safe order value to actually save on the new row.
    """
    query = model.query
    if filters:
        query = query.filter_by(**filters)

    existing_count = query.count()

    # Clamp: if requested position is beyond the end, just append at the end
    if requested_order > existing_count:
        requested_order = existing_count

    # Push down anything at or after the target position
    to_shift = query.filter(model.order >= requested_order).all()
    for row in to_shift:
        row.order += 1

    return requested_order


def reorder_on_update(model, item_id, old_order, new_order, filters=None):
    """When editing an existing row's order, close the gap it leaves behind
    and make room at its new position — handles moving up or down correctly."""
    if old_order == new_order:
        return new_order

    query = model.query
    if filters:
        query = query.filter_by(**filters)

    existing_count = query.filter(model.id != item_id).count()
    if new_order > existing_count:
        new_order = existing_count

    if new_order > old_order:
        # Moved down the list — shift everything between old and new position up by 1
        rows = query.filter(
            model.id != item_id,
            model.order > old_order,
            model.order <= new_order,
        ).all()
        for row in rows:
            row.order -= 1
    else:
        # Moved up the list — shift everything between new and old position down by 1
        rows = query.filter(
            model.id != item_id,
            model.order >= new_order,
            model.order < old_order,
        ).all()
        for row in rows:
            row.order += 1

    return new_order


def reorder_on_delete(model, deleted_order, filters=None):
    """After deleting a row, close the gap by shifting every row that came
    after it back by 1, so ordering stays contiguous (0,1,2,3...) with no holes."""
    query = model.query
    if filters:
        query = query.filter_by(**filters)

    rows = query.filter(model.order > deleted_order).all()
    for row in rows:
        row.order -= 1