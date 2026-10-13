# **3. Rule Definitions (Evidence-Coded)**

**Rule Set A: Pinggang Pinoy Portion Compliance**
"""

# pinggang_pinoy_rules.py

PINGGANG_PINOY = {
    "glow_vegetables_fruits": {
        "target_proportion": 0.50,  # 1/2 plate
        "tolerance": 0.10,  # ±10% acceptable
        "evidence": "DOST-FNRI Pinggang Pinoy: half plate fruits and vegetables [citation:13]",
        "severity": "MAJOR"
    },
    "go_carbohydrates": {
        "target_proportion": 0.33,  # 1/3 plate
        "tolerance": 0.10,
        "evidence": "Pinggang Pinoy: one-third carbohydrates [citation:3]",
        "severity": "MODERATE"
    },
    "grow_protein": {
        "target_proportion": 0.17,  # 1/6 plate
        "tolerance": 0.08,
        "evidence": "Pinggang Pinoy: one-sixth protein-rich foods [citation:13]",
        "severity": "MODERATE"
    }
}

"""**Rule Set B: Nutrient Thresholds (Clinical Rules)**"""

# clinical_nutrient_rules.py

CLINICAL_RULES = {
    "sodium_restriction": {
        "max_daily_mg": 2000,  # 2g sodium
        "evidence": "FNRI MNT Guidelines: Hypertension - sodium ≤2g/day [citation:11]",
        "severity": "CRITICAL",
        "applies_to": ["hypertension", "cardiovascular_risk"]
    },
    "added_sugar_limit": {
        "max_percent_calories": 10,  # WHO/NGF recommendation
        "evidence": "NGF: Limit sugar-rich foods [citation:14]",
        "severity": "MAJOR"
    },
    "saturated_fat_limit": {
        "max_percent_calories": 10,
        "evidence": "NGF: Limit fatty foods [citation:14]; Davao Transparency Ordinance thresholds [citation:5]",
        "severity": "MAJOR"
    },
    "fiber_minimum": {
        "min_daily_g": 20,  # For adults
        "evidence": "Pinggang Pinoy: vegetables/fruits provide fiber for regulation [citation:18]",
        "severity": "MODERATE"
    }
}

"""**Rule Set C: Davao City Institutional Rules (80% Healthy)**"""

# davao_institutional_rules.py

DAVAO_INSTITUTIONAL = {
    "healthy_food_ratio": {
        "min_percent": 80,  # 80% of items must be healthy
        "evidence": "Ordinance No. 0250-26: 80% of food sold should be healthy [citation:2]",
        "severity": "CRITICAL"
    },
    "prohibited_in_schools_hospitals": {
        "items": ["sugary_beverages", "deep_fried_snacks", "high_sodium_processed"],
        "evidence": "Davao Ordinance: sale of unhealthy foods strictly prohibited in schools and hospitals [citation:2]",
        "severity": "CRITICAL"
    },
    "minimally_processed_priority": {
        "target_percent": 70,
        "evidence": "Ordinance: nutrient-dense, minimally processed foods prioritized [citation:2]",
        "severity": "MAJOR"
    },
    "cultural_appropriateness": {
        "required": True,
        "local_foods": ["malunggay", "saluyot", "alugbati", "dried fish", "brown rice", "root_crops"],
        "evidence": "Ordinance: culturally appropriate foods required [citation:2]; Pinggang Pinoy local food examples [citation:15]",
        "severity": "MODERATE"
    }
}

"""**Rule Set D: Prohibited / Restricted Items**"""

# restricted_items_rules.py

RESTRICTED_ITEMS = {
    "high_sodium_processed": {
        "examples": ["instant_noodles", "canned_corned_beef", "processed_meats"],
        "action": "FLAG_WARNING",
        "evidence": "FNRI: Reduced consumption of processed foods to decrease sodium [citation:11]"
    },
    "sugar_sweetened_beverages": {
        "examples": ["soda", "sweetened_juice", "energy_drinks"],
        "action": "PROHIBIT_IN_INSTITUTIONS",
        "evidence": "Davao Ordinance: sugary beverages discouraged; Pinggang Pinoy: limit SSBs [citation:2][citation:18]"
    },
    "deep_fried_foods": {
        "action": "LIMIT",
        "evidence": "NGF: Limit fried foods [citation:14]"
    }
}

"""# **4. Implementation Blueprint**

**Data Model**
"""

# models.py

from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from enum import Enum

class FoodGroup(str, Enum):
    GO = "go"       # carbohydrates
    GROW = "grow"   # protein
    GLOW = "glow"   # vegetables/fruits

class Severity(str, Enum):
    INFO = "info"
    MODERATE = "moderate"
    MAJOR = "major"
    CRITICAL = "critical"

class FoodItem(BaseModel):
    name: str
    group: FoodGroup
    serving_grams: float
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    sodium_mg: float
    fiber_g: float
    added_sugar_g: float
    is_processed: bool = False
    is_fried: bool = False
    is_local: bool = False

class Meal(BaseModel):
    name: str
    items: List[FoodItem]

class MealPlan(BaseModel):
    plan_id: str
    patient_profile: Optional[str] = None  # "diabetic", "hypertensive", "general"
    meals: List[Meal]  # breakfast, lunch, dinner
    target_daily_calories: float = 2000

class ComplianceIssue(BaseModel):
    rule_id: str
    severity: Severity
    message: str
    evidence: str
    actual_value: Optional[float]
    threshold_value: Optional[float]

class ValidationResult(BaseModel):
    plan_id: str
    compliant: bool
    overall_score: float  # 0-100
    issues: List[ComplianceIssue]
    warnings: List[ComplianceIssue]

"""**Rule Engine Core**"""

# engine.py

class DavaoDietaryRuleEngine:
    """Evidence-based policy rule engine for Davao City dietary guidelines."""

    def __init__(self):
        self.rules = self._load_rules()
        self.food_db = FoodCompositionDB()  # FNRI Philippine Food Composition Table wrapper

    def validate_meal_plan(self, plan: MealPlan) -> ValidationResult:
        issues = []

        # Rule A: Pinggang Pinoy portions
        issues.extend(self._check_pinggang_portions(plan))

        # Rule B: Clinical nutrient thresholds
        if plan.patient_profile:
            issues.extend(self._check_clinical_rules(plan))

        # Rule C: Davao institutional 80% rule
        issues.extend(self._check_davao_80_percent(plan))

        # Rule D: Restricted items
        issues.extend(self._check_restricted_items(plan))

        # Rule E: General NGF compliance
        issues.extend(self._check_ngf_general(plan))

        # Calculate score
        score = self._calculate_score(issues)

        return ValidationResult(
            plan_id=plan.plan_id,
            compliant=not any(i.severity in [Severity.CRITICAL, Severity.MAJOR] for i in issues),
            overall_score=score,
            issues=[i for i in issues if i.severity in [Severity.CRITICAL, Severity.MAJOR]],
            warnings=[i for i in issues if i.severity in [Severity.MODERATE, Severity.INFO]]
        )

    def _check_pinggang_portions(self, plan: MealPlan) -> List[ComplianceIssue]:
        """Validate plate proportions against Pinggang Pinoy model."""
        issues = []

        for meal in plan.meals:
            total_grams = sum(item.serving_grams for item in meal.items)
            if total_grams == 0:
                continue

            group_grams = {g: 0 for g in FoodGroup}
            for item in meal.items:
                group_grams[item.group] += item.serving_grams

            # Check GLOW (should be ~50%)
            glow_pct = group_grams[FoodGroup.GLOW] / total_grams
            if not (0.40 <= glow_pct <= 0.60):
                issues.append(ComplianceIssue(
                    rule_id="PP_GLOW_PORTION",
                    severity=Severity.MAJOR,
                    message=f"Meal '{meal.name}': vegetables/fruits = {glow_pct:.0%}, target 50% (Pinggang Pinoy)",
                    evidence="Pinggang Pinoy: half the plate should be vegetables and fruits [citation:13]",
                    actual_value=glow_pct,
                    threshold_value=0.50
                ))

            # Check GO (should be ~33%)
            go_pct = group_grams[FoodGroup.GO] / total_grams
            if not (0.25 <= go_pct <= 0.42):
                issues.append(ComplianceIssue(
                    rule_id="PP_GO_PORTION",
                    severity=Severity.MODERATE,
                    message=f"Meal '{meal.name}': carbohydrates = {go_pct:.0%}, target 33%",
                    evidence="Pinggang Pinoy: one-third of plate should be Go foods [citation:3]",
                    actual_value=go_pct,
                    threshold_value=0.33
                ))

        return issues

    def _check_davao_80_percent(self, plan: MealPlan) -> List[ComplianceIssue]:
        """Davao Ordinance No. 0250-26: 80% of items must be healthy."""
        issues = []
        all_items = [item for meal in plan.meals for item in meal.items]
        if not all_items:
            return issues

        healthy_count = sum(1 for item in all_items if self._is_healthy(item))
        healthy_pct = healthy_count / len(all_items) * 100

        if healthy_pct < 80:
            issues.append(ComplianceIssue(
                rule_id="DAVAO_80_PERCENT",
                severity=Severity.CRITICAL,
                message=f"Only {healthy_pct:.0f}% of food items are classified as healthy. Minimum: 80%.",
                evidence="Davao City Ordinance No. 0250-26: 80% of food sold should be healthy [citation:2]",
                actual_value=healthy_pct,
                threshold_value=80
            ))

        return issues

    def _is_healthy(self, item: FoodItem) -> bool:
        """Classify food item as healthy per Davao/FNRI criteria."""
        # Unhealthy if: high sodium, high added sugar, high saturated fat, fried, or ultra-processed
        if item.is_fried:
            return False
        if item.sodium_mg > 400:  # per serving threshold
            return False
        if item.added_sugar_g > 10:
            return False
        if item.is_processed and item.sodium_mg > 300:
            return False
        return True

    def _check_clinical_rules(self, plan: MealPlan) -> List[ComplianceIssue]:
        """Apply clinical nutrition rules based on patient profile."""
        issues = []

        # Aggregate daily nutrients
        daily_sodium = sum(item.sodium_mg for meal in plan.meals for item in meal.items)

        if plan.patient_profile in ["hypertension", "hypertensive", "cardiovascular"]:
            if daily_sodium > 2000:
                issues.append(ComplianceIssue(
                    rule_id="CLINICAL_SODIUM",
                    severity=Severity.CRITICAL,
                    message=f"Daily sodium = {daily_sodium:.0f}mg. Hypertensive patients: max 2000mg.",
                    evidence="FNRI MNT Guidelines: Restriction of sodium intake to 2 grams a day [citation:11]",
                    actual_value=daily_sodium,
                    threshold_value=2000
                ))

        if plan.patient_profile in ["diabetes", "diabetic", "t2dm"]:
            daily_sugar = sum(item.added_sugar_g for meal in plan.meals for item in meal.items)
            if daily_sugar > 25:
                issues.append(ComplianceIssue(
                    rule_id="CLINICAL_SUGAR",
                    severity=Severity.CRITICAL,
                    message=f"Daily added sugar = {daily_sugar:.0f}g. Diabetic patients: limit to ~25g.",
                    evidence="FNRI MNT Guidelines: Dietary intervention for blood sugar control [citation:11]",
                    actual_value=daily_sugar,
                    threshold_value=25
                ))

        return issues

    def _check_restricted_items(self, plan: MealPlan) -> List[ComplianceIssue]:
        """Check for prohibited/restricted items per Davao ordinances."""
        issues = []
        prohibited = {"soda", "sugary_drink", "energy_drink", "candy", "chicharon"}

        for meal in plan.meals:
            for item in meal.items:
                if item.name.lower() in prohibited:
                    issues.append(ComplianceIssue(
                        rule_id="PROHIBITED_ITEM",
                        severity=Severity.CRITICAL,
                        message=f"'{item.name}' is prohibited in institutional settings",
                        evidence="Davao Ordinance: sale of unhealthy foods strictly prohibited in schools and hospitals [citation:2]"
                    ))

        return issues

"""**FastAPI Endpoint**"""

# Commented out IPython magic to ensure Python compatibility.
# %%writefile main.py
# # main.py
from fastapi import FastAPI, HTTPException
from models import MealPlan, ValidationResult
from engine import DavaoDietaryRuleEngine

app = FastAPI(
    title="Davao City Dietary Policy Validator",
    description="Evidence-based compliance engine for institutional meal plans per Davao City ordinances and national FNRI guidelines.",
    version="1.0.0"
)

engine = DavaoDietaryRuleEngine()

@app.post("/validate/meal-plan", response_model=ValidationResult)
async def validate_meal_plan(plan: MealPlan):
    """
    Validate a meal plan against:
    - Davao City Ordinance No. 0250-26 (Healthy Food Procurement)
    - Pinggang Pinoy portion model (DOST-FNRI)
    - Nutritional Guidelines for Filipinos
    - Clinical MNT guidelines (if patient profile provided)
    """
    return engine.validate_meal_plan(plan)

# @app.get("/policy/rules")
# async def get_active_rules():
#     """Return the full rule set with evidence citations."""
    return {
        "jurisdiction": "Davao City, Philippines",
        "policy_sources": [
            {
                "name": "Ordinance No. 0250-26",
                "title": "Healthy Food Procurement Ordinance of Davao City",
                "key_requirements": ["80% healthy food ratio", "prohibition in schools/hospitals", "minimally processed priority"]
            },
            {
                "name": "Pinggang Pinoy",
                "authority": "DOST-FNRI",
                "key_requirements": ["½ plate Glow", "⅓ plate Go", "⅙ plate Grow"]
            },
            {
                "name": "Nutritional Guidelines for Filipinos",
                "authority": "NNC/FNRI",
                "key_requirements": ["variety", "vegetables/fruits daily", "limit salty/fatty/sugary", "iodized salt"]
            }
        ]
    }

!pip install matplotlib-venn

!apt-get -qq install -y libfluidsynth1

# https://pypi.python.org/pypi/libarchive
!apt-get update -qq && apt-get -qq install -y libarchive-dev && pip install -U libarchive
import libarchive

# https://pypi.python.org/pypi/pydot
!apt-get -qq install -y graphviz && pip install pydot
import pydot

!pip install cartopy
import cartopy
