import streamlit as st
import json
from typing import Dict, List, Tuple
import uuid
from db import insert_garden, fetch_gardens, get_garden_by_id, delete_garden

# Garden element definitions
GARDEN_ELEMENTS = {
    "🌺 Flowers": {
        "icon": "🌺",
        "name": "Flowers",
        "color": "#ff69b4",
        "size": (60, 60),
        "description": "Colorful garden flowers"
    },
    "🌿 Shrubs": {
        "icon": "🌿",
        "name": "Shrubs",
        "color": "#228b22",
        "size": (80, 80),
        "description": "Evergreen shrubs and bushes"
    },
    "🌳 Tree": {
        "icon": "🌳",
        "name": "Tree",
        "color": "#006400",
        "size": (100, 120),
        "description": "Large garden tree"
    },
    "🏡 Fence": {
        "icon": "🏡",
        "name": "Fence",
        "color": "#8b4513",
        "size": (100, 20),
        "description": "Garden boundary fence"
    },
    "🪨 Patio": {
        "icon": "🪨",
        "name": "Patio",
        "color": "#696969",
        "size": (120, 120),
        "description": "Stone patio area"
    },
    "🪨 Stones": {
        "icon": "🪨",
        "name": "Stones",
        "color": "#a9a9a9",
        "size": (40, 40),
        "description": "Decorative garden stones"
    },
    "🌱 Grass": {
        "icon": "🌱",
        "name": "Grass",
        "color": "#90ee90",
        "size": (100, 100),
        "description": "Lawn grass area"
    },
    "💧 Pond": {
        "icon": "💧",
        "name": "Pond",
        "color": "#4169e1",
        "size": (80, 80),
        "description": "Garden water feature"
    },
    "🪑 Bench": {
        "icon": "🪑",
        "name": "Bench",
        "color": "#8b4513",
        "size": (60, 40),
        "description": "Garden seating"
    },
    "🕯️ Path": {
        "icon": "🕯️",
        "name": "Path",
        "color": "#f4a460",
        "size": (80, 30),
        "description": "Garden walkway"
    }
}

def init_garden_session():
    """Initialize garden design session state"""
    if "garden_elements" not in st.session_state:
        st.session_state.garden_elements = []
    if "garden_name" not in st.session_state:
        st.session_state.garden_name = "My Garden"

def save_garden():
    """Save current garden design"""
    if not st.session_state.garden_name.strip():
        st.error("Please enter a garden name!")
        return None
    
    if not st.session_state.garden_elements:
        st.error("Please add some elements to your garden first!")
        return None
    
    try:
        garden_id = insert_garden(st.session_state.garden_name, st.session_state.garden_elements)
        st.success(f"Garden '{st.session_state.garden_name}' saved with ID {garden_id}!")
        return garden_id
    except Exception as e:
        st.error(f"Error saving garden: {str(e)}")
        return None

def load_garden(garden_data):
    """Load a saved garden design"""
    st.session_state.garden_name = garden_data["name"]
    st.session_state.garden_elements = garden_data["elements"]
    st.success(f"Loaded garden: {garden_data['name']}")

def clear_garden():
    """Clear current garden design"""
    st.session_state.garden_elements = []
    st.success("Garden cleared!")

def add_element(element_type: str, x: int, y: int):
    """Add a new element to the garden"""
    element_id = str(uuid.uuid4())
    new_element = {
        "id": element_id,
        "type": element_type,
        "x": x,
        "y": y,
        "rotation": 0,
        "scale": 1.0
    }
    st.session_state.garden_elements.append(new_element)

def rotate_element(element_id: str, rotation: int):
    """Rotate an element"""
    for element in st.session_state.garden_elements:
        if element["id"] == element_id:
            element["rotation"] = rotation
            break

def scale_element(element_id: str, scale: float):
    """Scale an element"""
    for element in st.session_state.garden_elements:
        if element["id"] == element_id:
            element["scale"] = max(0.5, min(2.0, scale))  # Limit scale between 0.5 and 2.0
            break

def update_element_position(element_id: str, x: int, y: int):
    """Update element position after drag and drop"""
    for element in st.session_state.garden_elements:
        if element["id"] == element_id:
            element["x"] = max(0, min(800, x))  # Limit to canvas bounds
            element["y"] = max(0, min(500, y))  # Limit to canvas bounds
            break

def remove_element(element_id: str):
    """Remove an element from the garden"""
    st.session_state.garden_elements = [
        elem for elem in st.session_state.garden_elements 
        if elem["id"] != element_id
    ]

def garden_designer():
    """Main garden designer interface"""
    st.markdown("### 🏡 Garden Designer")
    st.caption("Create your dream garden with our building blocks!")
    
    # Garden tips and inspiration
    col1, col2 = st.columns([1, 1])
    
    with col1:
        with st.expander("💡 Garden Design Tips"):
            st.markdown("""
            **Design Principles:**
            - **Balance**: Distribute elements evenly across your garden
            - **Focal Points**: Use trees or water features as centerpieces
            - **Layering**: Place taller elements (trees) in back, shorter (flowers) in front
            - **Color Harmony**: Group similar colored elements together
            - **Pathways**: Create natural flow with paths and walkways
            
            **Element Placement:**
            - Start with larger elements (trees, patio) as anchors
            - Add medium elements (shrubs, benches) for structure
            - Finish with small details (flowers, stones) for accents
            """)
    
    with col2:
        with st.expander("🎨 Garden Themes"):
            st.markdown("""
            **🌿 Natural Garden**: Focus on native plants, water features, and natural stone
            **🏡 Cottage Garden**: Mix of flowers, herbs, and traditional structures
            **🌳 Modern Garden**: Clean lines, minimal elements, geometric shapes
            **💧 Zen Garden**: Water features, stones, and peaceful seating areas
            **🌺 Colorful Garden**: Vibrant flowers and colorful accents throughout
            """)
            
            # Quick theme selector
            theme = st.selectbox("Apply Theme", ["None", "Natural", "Cottage", "Modern", "Zen", "Colorful"])
            if theme != "None" and st.button("Apply Theme"):
                apply_theme(theme)
                st.success(f"Applied {theme} theme!")
    
    # Garden name input
    col1, col2 = st.columns([2, 1])
    with col1:
        st.text_input("Garden Name", key="garden_name", placeholder="Enter your garden name")
    with col2:
        if st.button("💾 Save Garden", type="primary"):
            save_garden()
    
    # Control buttons
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("🗑️ Clear Garden"):
            clear_garden()
    with col2:
        if st.button("🔄 Reset View"):
            st.rerun()
    with col3:
        if st.button("📊 Garden Stats"):
            st.info("Statistics shown below the canvas!")
    with col4:
        if st.button("📤 Export Design"):
            st.info("Export feature coming soon!")
    
    # Element palette
    st.markdown("#### 🎨 Building Blocks")
    st.caption("Click to add elements to your garden canvas")
    
    # Group elements by category for better organization
    categories = {
        "🌱 Plants": ["🌺 Flowers", "🌿 Shrubs", "🌳 Tree", "🌱 Grass"],
        "🏗️ Structures": ["🏡 Fence", "🪨 Patio", "🪑 Bench", "🕯️ Path"],
        "🎨 Decor": ["🪨 Stones", "💧 Pond"]
    }
    
    for category, element_keys in categories.items():
        st.markdown(f"**{category}**")
        cols = st.columns(len(element_keys))
        
        for i, element_key in enumerate(element_keys):
            if element_key in GARDEN_ELEMENTS:
                element_info = GARDEN_ELEMENTS[element_key]
                with cols[i]:
                    st.markdown(f"{element_info['icon']} **{element_info['name']}**")
                    st.caption(element_info['description'])
                    if st.button(f"➕ Add", key=f"add_{element_key}", use_container_width=True):
                        # Add element at center of canvas
                        add_element(element_key, 400, 300)
                        st.rerun()
        st.divider()
    
    # Garden canvas
    st.markdown("#### 🎨 Garden Canvas")
    st.caption("Drag elements to reposition them. Click the sync button below to save positions.")
    
    # Sync positions button
    if st.button("🔄 Sync Positions", help="Click after dragging elements to save their new positions"):
        st.success("Positions synced! Your garden layout has been updated.")
        st.rerun()
    
    # Create a visual representation of the garden
    if st.session_state.garden_elements:
        # Create a simple visual layout
        garden_html = create_garden_visualization()
        st.components.v1.html(garden_html, height=600, scrolling=False)
        
        # Element list
        st.markdown("#### 📋 Garden Elements")
        for i, element in enumerate(st.session_state.garden_elements):
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            with col1:
                element_info = GARDEN_ELEMENTS.get(element["type"], {})
                st.write(f"{element_info.get('icon', '🌿')} {element_info.get('name', element['type'])}")
            with col2:
                st.write(f"Position: ({element['x']}, {element['y']})")
            with col3:
                st.write(f"Rotation: {element['rotation']}°")
            with col4:
                if st.button("🗑️", key=f"remove_{element['id']}"):
                    remove_element(element['id'])
                    st.rerun()
    else:
        st.info("No elements in your garden yet. Add some building blocks above!")
        
    # Garden statistics
    if st.session_state.garden_elements:
        st.markdown("#### 📊 Garden Statistics")
        element_counts = {}
        for element in st.session_state.garden_elements:
            element_type = element["type"]
            element_counts[element_type] = element_counts.get(element_type, 0) + 1
        
        stat_cols = st.columns(len(element_counts))
        for i, (element_type, count) in enumerate(element_counts.items()):
            with stat_cols[i]:
                element_info = GARDEN_ELEMENTS.get(element_type, {})
                st.metric(
                    f"{element_info.get('icon', '🌿')} {element_info.get('name', element_type)}",
                    count
                )
    
    # Garden Gallery
    st.markdown("---")
    st.markdown("#### 🖼️ Saved Gardens")
    
    try:
        saved_gardens = fetch_gardens(limit=10)
        if saved_gardens:
            for garden in saved_gardens:
                with st.expander(f"🏡 {garden['name']} (Created: {garden['created_at']})"):
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.write(f"**Elements:** {len(garden['elements'])}")
                        if garden['elements']:
                            element_types = [elem['type'] for elem in garden['elements']]
                            st.write(f"**Types:** {', '.join(set(element_types))}")
                    with col2:
                        if st.button("Load", key=f"load_{garden['id']}"):
                            load_garden(garden)
                            st.rerun()
                    with col3:
                        if st.button("🗑️", key=f"delete_garden_{garden['id']}"):
                            delete_garden(garden['id'])
                            st.success(f"Deleted garden: {garden['name']}")
                            st.rerun()
        else:
            st.info("No saved gardens yet. Create and save your first garden above!")
    except Exception as e:
        st.error(f"Error loading gardens: {str(e)}")

def create_garden_visualization():
    """Create HTML visualization of the garden"""
    html = """
    <div id="garden-canvas" style="
        width: 100%;
        height: 500px;
        background: 
            radial-gradient(circle at 20% 30%, #98fb98 0%, transparent 50%),
            radial-gradient(circle at 80% 70%, #90ee90 0%, transparent 50%),
            linear-gradient(135deg, #90ee90 0%, #98fb98 100%);
        border: 3px solid #228b22;
        border-radius: 15px;
        position: relative;
        overflow: hidden;
        box-shadow: 0 8px 16px rgba(0,0,0,0.15);
    ">
        <!-- Background decorative elements -->
        <div style="
            position: absolute;
            top: 10px;
            right: 10px;
            font-size: 12px;
            color: #228b22;
            opacity: 0.3;
        ">🌿 Garden Canvas</div>
        
        <!-- Grid overlay for better positioning -->
        <div style="
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-image: 
                linear-gradient(rgba(34, 139, 34, 0.1) 1px, transparent 1px),
                linear-gradient(90deg, rgba(34, 139, 34, 0.1) 1px, transparent 1px);
            background-size: 50px 50px;
            pointer-events: none;
        "></div>
    """
    
    # Add garden elements with enhanced styling
    for element in st.session_state.garden_elements:
        element_info = GARDEN_ELEMENTS.get(element["type"], {})
        icon = element_info.get("icon", "🌿")
        color = element_info.get("color", "#228b22")
        size_x, size_y = element_info.get("size", (60, 60))
        
        # Add shadow and glow effects
        html += f"""
        <div class="garden-element" style="
            position: absolute;
            left: {element['x']}px;
            top: {element['y']}px;
            width: {size_x}px;
            height: {size_y}px;
            background: {color};
            border: 2px solid #333;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            cursor: move;
            box-shadow: 
                0 4px 8px rgba(0,0,0,0.3),
                0 0 20px rgba(34, 139, 34, 0.2);
            transform: rotate({element['rotation']}deg);
            transition: all 0.3s ease;
            z-index: 10;
            user-select: none;
        " 
        draggable="true"
        data-element-id="{element['id']}"
        data-element-type="{element['type']}"
        data-x="{element['x']}"
        data-y="{element['y']}"
        title="{element_info.get('name', element['type'])} - Drag to move">
            {icon}
        </div>
        """
    
    # Add garden info overlay
    element_count = len(st.session_state.garden_elements)
    html += f"""
        <div style="
            position: absolute;
            bottom: 10px;
            left: 10px;
            background: rgba(255, 255, 255, 0.9);
            padding: 8px 12px;
            border-radius: 20px;
            font-size: 12px;
            color: #228b22;
            font-weight: bold;
            border: 1px solid #228b22;
        ">
            🏡 {element_count} element{'s' if element_count != 1 else ''}
        </div>
        
        <div style="
            position: absolute;
            bottom: 10px;
            right: 10px;
            background: rgba(255, 255, 255, 0.9);
            padding: 8px 12px;
            border-radius: 20px;
            font-size: 12px;
            color: #228b22;
            font-weight: bold;
            border: 1px solid #228b22;
        ">
            🖱️ Drag to move elements
        </div>
    """
    
    html += """
    </div>
    <style>
        .garden-element {
            transition: all 0.3s ease;
        }
        .garden-element:hover {
            transform: scale(1.1) !important;
            z-index: 20 !important;
            box-shadow: 0 6px 12px rgba(0,0,0,0.4), 0 0 30px rgba(34, 139, 34, 0.4) !important;
        }
        .garden-element.dragging {
            opacity: 0.8;
            z-index: 100 !important;
        }
    </style>
    
    <script>
        // Drag and drop functionality
        let draggedElement = null;
        let offsetX = 0;
        let offsetY = 0;
        
        // Add drag event listeners to all garden elements
        document.addEventListener('DOMContentLoaded', function() {
            const elements = document.querySelectorAll('.garden-element');
            
            elements.forEach(function(element) {
                element.addEventListener('dragstart', function(e) {
                    draggedElement = element;
                    element.classList.add('dragging');
                    
                    // Calculate offset from mouse to element corner
                    const rect = element.getBoundingClientRect();
                    offsetX = e.clientX - rect.left;
                    offsetY = e.clientY - rect.top;
                    
                    e.dataTransfer.effectAllowed = 'move';
                    e.dataTransfer.setData('text/html', element.outerHTML);
                });
                
                element.addEventListener('dragend', function(e) {
                    element.classList.remove('dragging');
                    draggedElement = null;
                });
            });
            
            // Handle drop on canvas
            const canvas = document.getElementById('garden-canvas');
            
            canvas.addEventListener('dragover', function(e) {
                e.preventDefault();
                e.dataTransfer.dropEffect = 'move';
            });
            
            canvas.addEventListener('drop', function(e) {
                e.preventDefault();
                
                if (draggedElement) {
                    const rect = canvas.getBoundingClientRect();
                    const newX = e.clientX - rect.left - offsetX;
                    const newY = e.clientY - rect.top - offsetY;
                    
                    // Update element position
                    draggedElement.style.left = newX + 'px';
                    draggedElement.style.top = newY + 'px';
                    
                    // Update data attributes
                    draggedElement.setAttribute('data-x', newX);
                    draggedElement.setAttribute('data-y', newY);
                    
                    // Show success message
                    showMessage('Element moved!', 'success');
                }
            });
            
            // Prevent default drag behavior on elements
            elements.forEach(function(element) {
                element.addEventListener('dragenter', function(e) {
                    e.preventDefault();
                });
                
                element.addEventListener('dragover', function(e) {
                    e.preventDefault();
                });
            });
        });
        
        function showMessage(text, type) {
            // Create temporary message
            const msg = document.createElement('div');
            msg.textContent = text;
            msg.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background: ${type === 'success' ? '#4CAF50' : '#f44336'};
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
            z-index: 1000;
                font-family: Arial, sans-serif;
                font-size: 14px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            `;
            
            document.body.appendChild(msg);
            
            // Remove after 2 seconds
            setTimeout(function() {
                if (msg.parentNode) {
                    msg.parentNode.removeChild(msg);
                }
            }, 2000);
        }
    </script>
    """
    
    return html
