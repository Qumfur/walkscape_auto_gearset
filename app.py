import streamlit as st
import streamlit.components.v1 as components
import json
import math
from typing import List, Dict, Optional

from utils import parse_csv_to_items, parse_csv_to_activities, calculate_steps
from gear_optimizer import GearOptimizer, OPTIMAZATION_TARGET
from export import export_gearset

st.set_page_config(
    page_title="WalkScape Gear Optimizer",
    layout="wide",
    initial_sidebar_state="expanded"
)

def get_xp_for_level(level: int) -> int:
    """Standard XP curve formula (internal)."""
    total = 0
    for i in range(1, level):
        total += math.floor(i + 300 * (2 ** (i / 7.0)))
    return math.floor(total / 4)

def calculate_level_from_xp(current_xp: int) -> int:
    """Reverse lookup: Finds skill level based on XP."""
    # Optimization: Simple iterative check since max level is usually < 150
    for lvl in range(1, 150):
        if get_xp_for_level(lvl + 1) > current_xp:
            return lvl
    return 150

def calculate_char_level_from_steps(current_steps: int) -> int:
    """
    Specific formula for Character Level based on Steps.
    Step Req = (Standard_XP_Curve / 4).floor() * 4.6
    """
    for lvl in range(1, 120):
        # Calculate steps required for NEXT level
        xp_req_standard = get_xp_for_level(lvl + 1)
        steps_req = math.floor(xp_req_standard) * 4.6
        
        if steps_req > current_steps:
            return lvl
    return 120

# --- 3. Data Loading ---
@st.cache_data
def load_data():
    items_file = "items.csv"
    activity_file = "activities.csv"
    recipes_file = "recipes.csv"
    
    all_items = parse_csv_to_items(items_file)
    activities = parse_csv_to_activities(activity_file, recipes_file)
    return all_items, activities

def filter_user_items(all_items, user_data: Dict):
    try:
        owned_names = set()
        owned_names.update(user_data.get("bank", {}).keys())
        owned_names.update(user_data.get("inventory", {}).keys())
        if "gear" in user_data:
            equipped = {v for v in user_data["gear"].values() if v}
            owned_names.update(equipped)
        return [item for item in all_items if item.export_name in owned_names]
    except Exception:
        return all_items

# --- 4. Main App ---
def main():
    st.title("🛡️ WalkScape Gear Optimizer")
    all_items_raw, activities = load_data()
    
    # --- State Management for Levels ---
    # We store these to allow the UI to react to the JSON immediately
    user_data = None
    calculated_char_lvl = 99
    user_skills_map = {} # {'agility': 4771615, ...}

    # --- Sidebar ---
    with st.sidebar:
        st.header("User Settings")
        
        # 1. JSON Input
        user_json_input = st.text_area(
            "Paste User JSON", 
            height=100,
            placeholder='{"name": "Kozz", "steps": 10121691, "skills": {...}}'
        )
        
        # 2. Parse JSON & Calculate Levels
        valid_json = False
        if user_json_input.strip():
            try:
                user_data = json.loads(user_json_input)
                valid_json = True
                
                # --- AUTO-CALC CHARACTER LEVEL ---
                steps = user_data.get("steps", 0)
                calculated_char_lvl = calculate_char_level_from_steps(steps)
                user_skills_map = user_data.get("skills", {})
                
                st.success(f"Loaded: {user_data.get('name', 'Player')}")
            except json.JSONDecodeError:
                st.error("Invalid JSON")

        use_owned = st.checkbox("Only use owned items", value=valid_json)

        st.divider()
        
        # 3. Level Inputs (Conditional)
        st.subheader("Stats")
        
        if valid_json:
            # READ-ONLY MODE
            st.info(f"**Character Level:** {calculated_char_lvl}\n\n*(Calculated from {user_data.get('steps',0):,} steps)*")
            player_lvl = calculated_char_lvl
        else:
            # MANUAL MODE
            player_lvl = st.number_input("Character Level", value=99, min_value=1, max_value=99)

        # Skill level is handled dynamically in the main column based on activity selection
        # We just keep a placeholder here if needed, or hide it.
        if not valid_json:
            manual_skill_lvl = st.number_input("Skill Level (Default)", value=99)
        
        st.divider()
        wiki_url = st.text_input("Iframe URL", value="https://gear.walkscape.app")

    # --- Item Filtering ---
    if use_owned and user_data:
        available_items = filter_user_items(all_items_raw, user_data)
        st.caption(f"Status: Using {len(available_items)} owned items.")
    else:
        available_items = all_items_raw
        st.caption(f"Status: Using ALL {len(available_items)} items.")

    # --- Main Interface ---
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        act_map = {a.activity: a for a in activities}
        act_names = sorted(list(act_map.keys()))
        
        selected_act_name = st.selectbox(
            "Select Activity", 
            options=act_names,
            index=None,
            placeholder="Search activity..."
        )

    # --- Determine Skill Level ---
    # Logic: If JSON is loaded, try to find the skill level for the selected activity.
    # Otherwise, fall back to manual input.
    final_skill_lvl = 99 # Default
    
    if selected_act_name:
        activity = act_map[selected_act_name]
        req_skill = activity.skill  # e.g. "Agility", "Mining"
        
        if valid_json and req_skill:
            # Look up XP in user_skills_map (keys are likely lowercase)
            skill_key = req_skill.lower()
            skill_xp = user_skills_map.get(skill_key, 0)
            
            # Calculate Level from XP
            final_skill_lvl = calculate_level_from_xp(skill_xp)
            
            # Display the auto-detected level
            st.info(f"🎯 **Skill:** {req_skill} | **Level:** {final_skill_lvl} (derived from {skill_xp:,} XP)")
        elif not valid_json:
            # Use the manual sidebar input
            final_skill_lvl = manual_skill_lvl
    
    with col2:
        target_options = {t.name.replace('_', ' ').title(): t for t in OPTIMAZATION_TARGET}
        selected_target_key = st.selectbox("Target", options=list(target_options.keys()))
        selected_target = target_options[selected_target_key]

    with col3:
        st.write("") 
        st.write("") 
        run_opt = st.button("🚀 Optimize", type="primary", use_container_width=True)

    st.divider()

    # --- Optimization ---
    if run_opt and selected_act_name:
        activity = act_map[selected_act_name]
        
        with st.spinner(f"Optimizing for {selected_act_name}..."):
            optimizer = GearOptimizer(available_items)
            best_gear = optimizer.optimize(
                activity, 
                player_level=player_lvl, 
                player_skill_level=final_skill_lvl, # Uses the auto-calculated level
                optimazation_target=selected_target
            )

        # Stats
        stats = best_gear.get_stats(activity.skill)
        final_steps = calculate_steps(
            activity, final_skill_lvl, stats["work_efficiency"], 
            stats["flat_step_reduction"], stats["percent_step_reduction"]
        )
        
        xp_mult = 1.0 + stats["xp_percent"]
        total_xp = ((activity.base_xp or 0 * xp_mult) + stats["flat_xp"]) * (1.0 + stats["double_action"])
        
        # Metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Steps/Action", f"{final_steps}", delta=f"Base: {activity.base_steps}", delta_color="inverse")
        m2.metric("XP/Action", f"{total_xp:.2f}")
        m3.metric("Double Action", f"{stats['double_action']*100:.1f}%")
        m4.metric("Work Eff.", f"{stats['work_efficiency']*100:.1f}%")

        # Loadout Grid
        st.subheader("Loadout")
        gear_slots = [
            ("Head", best_gear.head), ("Chest", best_gear.chest), ("Legs", best_gear.legs), ("Feet", best_gear.feet),
            ("Back", best_gear.back), ("Cape", best_gear.cape), ("Neck", best_gear.neck), ("Hands", best_gear.hands),
            ("Ring 1", best_gear.rings[0] if len(best_gear.rings) > 0 else None),
            ("Ring 2", best_gear.rings[1] if len(best_gear.rings) > 1 else None),
            ("Primary", best_gear.primary), ("Secondary", best_gear.secondary)
        ]

        cols = st.columns(4)
        for i, (slot_name, item) in enumerate(gear_slots):
            with cols[i % 4]:
                if item:
                    st.success(f"**{slot_name}**\n\n{item.name}")
                else:
                    st.markdown(f"**{slot_name}**\n\nEmpty")

        if best_gear.tools:
            st.info("**Tools:** " + ", ".join([t.name for t in best_gear.tools]))

        st.subheader("Export Code")
        st.code(export_gearset(best_gear), language="json")

    elif run_opt:
        st.error("Select an activity.")

    # --- Iframe ---
    st.markdown("---")
    components.iframe(wiki_url, height=900, scrolling=True)

if __name__ == "__main__":
    main()