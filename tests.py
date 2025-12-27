import unittest
from models import Activity
from utils import calculate_steps

class TestWorkEfficiency(unittest.TestCase):
    def setUp(self):
        # Scenario 1: Hut Jumping (Base 53, Min 36)
        self.hut_jumping = Activity(
            activity="Hut Jumping",
            base_steps=53,
            min_steps=36,
            skill_level=25,
            max_work_efficiency=0.50, # Derived from Base/Min
            skill="Agility"
        )
        
        # Scenario 2: Port Agility from Screenshot (Base 110)
        # We use a high max_eff to ensure our test values aren't capped unexpectedly
        self.guard_duty = Activity(
            activity="Port Agility",
            base_steps=110,
            min_steps=10, 
            skill_level=55,
            max_work_efficiency=5.0, 
            skill="Agility"
        )

    def test_scenario_1_min_skills_no_gear(self):
        """Level 25 (Min), No Gear -> Expect 53 Steps"""
        steps = calculate_steps(
            activity=self.hut_jumping,
            player_skill_level=25,
            player_work_efficiency=0.0,
            player_minus_steps=0,
            player_minus_steps_percent=0.0
        )
        self.assertEqual(steps, 53)

    def test_scenario_2_skill_over_min_no_gear(self):
        """Level 40 (+15 lvls), No Gear -> Expect 45 Steps"""
        # Calculation: 15 levels * 1.25% = 18.75% eff.
        # 53 / 1.1875 = 44.63 -> ceil -> 45
        steps = calculate_steps(
            activity=self.hut_jumping,
            player_skill_level=40,
            player_work_efficiency=0.0,
            player_minus_steps=0,
            player_minus_steps_percent=0.0
        )
        self.assertEqual(steps, 45)

    def test_scenario_3_skill_over_min_with_gear(self):
        """Level 40, Walking Stick (+5%) -> Expect 43 Steps"""
        # Calculation: 18.75% (Level) + 5% (Gear) = 23.75%
        # 53 / 1.2375 = 42.82 -> ceil -> 43
        steps = calculate_steps(
            activity=self.hut_jumping,
            player_skill_level=40,
            player_work_efficiency=0.05,
            player_minus_steps=0,
            player_minus_steps_percent=0.0
        )
        self.assertEqual(steps, 43)

    def test_scenario_4_eff_over_max(self):
        """Level 50, High Gear (+50%) -> Expect 36 Steps (Capped)"""
        # Calculation:
        # Level: 50 - 25 = 25 lvls -> 31.25% (Capped at 25% internal max)
        # Gear: 50%
        # Total Raw: 75%. Activity Cap: 50%.
        # 53 / 1.50 = 35.33 -> ceil -> 36
        steps = calculate_steps(
            activity=self.hut_jumping,
            player_skill_level=50,
            player_work_efficiency=0.50,
            player_minus_steps=0,
            player_minus_steps_percent=0.0
        )
        self.assertEqual(steps, 36)

    def test_scenario_5_screenshot_integration(self):
        """
        Real-world test from screenshot:
        Base: 110, Lvl 88 (Req 55), Eff +108%, Steps -5% & -20.
        Expected Result: 31 Steps.
        """
        # Screenshot Total Eff: +108% (1.08)
        # Level Contribution: (88 - 55) * 1.25% = 41.25% -> Capped at 25% (0.25)
        # Implied Gear/Buff Efficiency: 1.08 - 0.25 = 0.83 (83%)
        
        steps = calculate_steps(
            activity=self.guard_duty,
            player_skill_level=88,
            player_work_efficiency=0.83, 
            player_minus_steps=20,       
            player_minus_steps_percent=0.05 
        )
        
        # Verify:
        # 1. Multiplier: 1 + 1.08 = 2.08
        # 2. Base: 110 / 2.08 = 52.88
        # 3. Percent Redux: 52.88 * 0.95 = 50.24
        # 4. Ceil: 51
        # 5. Flat Redux: 51 - 20 = 31
        self.assertEqual(steps, 31)

if __name__ == '__main__':
    unittest.main()