inputs = (
  ("Numeric input", 15.0),
  ("Numeric range", (4, -128, 128)),
  ("Block Selector", "blocktype"),
  ("Checkbox", True),
  ("Select options", ("option1", "option2", "option3")),
)


def perform(level, box, options):
    print("Running template filter", __name__)