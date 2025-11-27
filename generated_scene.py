import numpy as np
from manim import *

class GenScene(Scene):
    def construct(self):
        # 1. Setup the scene with axes
        axes = Axes(
            x_range=[-1, 5, 1],
            y_range=[-1, 4, 1],
            x_length=7,
            y_length=5,
            axis_config={"include_tip": False},
        )
        self.add(axes)

        # 2. Define vector coordinates
        vec_a_coords = [3, 1, 0]
        vec_b_coords = [1, 2, 0]
        vec_c_coords = [v1 + v2 for v1, v2 in zip(vec_a_coords, vec_b_coords)] # Correctly adds coordinates

        # 3. Create initial vector mobjects and labels
        vec_a = Vector(vec_a_coords, color=BLUE)
        vec_b = Vector(vec_b_coords, color=YELLOW)
        label_a = MathTex(r"\vec{a}").next_to(vec_a.get_tip(), RIGHT, buff=0.1)
        label_b = MathTex(r"\vec{b}").next_to(vec_b.get_tip(), UP, buff=0.1)

        # 4. Animate the first two vectors appearing from the origin
        self.play(GrowArrow(vec_a), Write(label_a))
        self.wait(0.5)
        self.play(GrowArrow(vec_b), Write(label_b))
        self.wait(1)

        # 5. Animate moving vector b to the tip of vector a
        vec_b_shifted = vec_b.copy().shift(vec_a.get_end())
        label_b_shifted = label_b.copy().next_to(vec_b_shifted.get_tip(), UP, buff=0.1)

        self.play(
            Transform(vec_b, vec_b_shifted),
            Transform(label_b, label_b_shifted)
        )
        self.wait(0.5)

        # 6. Draw the resultant vector c
        vec_c = Vector(vec_c_coords, color=RED)
        label_c = MathTex(r"\vec{c} = \vec{a} + \vec{b}").next_to(vec_c.get_tip(), DOWN, buff=0.2).scale(0.8)
        
        self.play(GrowArrow(vec_c))
        self.play(Write(label_c))
        self.wait(2)
