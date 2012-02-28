# scorecomment_lib
try:
    import erp.model.testing as tst
except ImportError:
    import portal.model.testing as tst

def fog1142():
    # get the comment set to update. In this case delta uses the default with level
    comment_set = tst.ScoreCommentSet.get(4)

    for comment in comment_set.comments:
        # only update the active comments, 
        # if the category is archived, the comment won't be used
        if not comment.archived and not comment.category.archived:
            # we only want to do the change if the category name is in the full text
            if comment.category.name in comment.full_text:
                comment.full_text = comment.full_text[len(comment.category.name):].lstrip()
