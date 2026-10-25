# Model class name, for example cable or solid_debris.
string label

# Model confidence in the range [0, 1].
float32 confidence

# Bounding box in source-frame pixels (x_min, y_min, x_max, y_max).
float32 x_min_px
float32 y_min_px
float32 x_max_px
float32 y_max_px

# Bounding-box center and size, normalized to [0, 1] relative to frame size.
float32 center_x_norm
float32 center_y_norm
float32 width_norm
float32 height_norm

# Advisory only: clean, avoid, avoid_and_review, or observe.
string suggested_action
