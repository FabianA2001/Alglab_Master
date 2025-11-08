import { Streamlit, RenderData } from "streamlit-component-lib"
// does the order matter?
import "./shift_plan_config.js"; // this will be ran when imported
import shiftPlanTable, { initShiftPlanTable } from "./shift_plan_table.js"; // 

/**
 * The component's render function. This will be called immediately after
 * the component is initially loaded, and then again every time the
 * component gets new data from Python.
 */
function onRender(event: Event): void {
  // Get the RenderData from the event
  const data = (event as CustomEvent<RenderData>).detail

  // RenderData.args is the JSON dictionary of arguments sent from the
  // Python script.
  let name = data.args["name"]
  console.log("Render data received:", data.args)
  if (data.args["render_option"] == "shift_plan_solution"){
    let shift_plan_solution = JSON.parse(data.args["data"])
    console.log("Shift plan solution received:", shift_plan_solution)
    if (!document.getElementById('shift-plan-app')) {
      // Dynamically add the HTML for the shift plan app
      const shiftPlanAppHTML = `
        <div id="shift-plan-app">
          <div class="filter-container">
            <input 
              type="text" 
              id="searchInput" 
              class="filter-input" 
              placeholder="Nach Mitarbeiter suchen..."
            >
          </div>
          <div class="shift-plan-container">
            <table class="shift-plan-table" id="shiftPlanTable">
              <thead>
                <tr id="headerRow"></tr>
              </thead>
              <tbody id="tableBody"></tbody>
            </table>
          </div>
          <div class="table-info" id="tableInfo"></div>
        </div>
      `;

      // Insert the HTML into the body or a specific container
      document.body.insertAdjacentHTML('beforeend', shiftPlanAppHTML);
    }
    // Initialize the shift plan table with the provided solution data
    initShiftPlanTable(shift_plan_solution)
    const searchInput = document.getElementById('searchInput') as HTMLInputElement;

    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const searchValue = searchInput.value; // No more TypeScript error
            console.log('Search Value:', searchValue);
            // Send the value back to Streamlit
            Streamlit.setComponentValue(searchValue);
        });
    } else {
        console.error('Search input not found.');
    }
  }

  // We tell Streamlit to update our frameHeight after each render event, in
  // case it has changed. (This isn't strictly necessary for the example
  // because our height stays fixed, but this is a low-cost function, so
  // there's no harm in doing it redundantly.)
  Streamlit.setFrameHeight()
}

// Attach our `onRender` handler to Streamlit's render event.
Streamlit.events.addEventListener(Streamlit.RENDER_EVENT, onRender)

// Tell Streamlit we're ready to start receiving data. We won't get our
// first RENDER_EVENT until we call this function.
Streamlit.setComponentReady()

// Finally, tell Streamlit to update our initial height. We omit the
// `height` parameter here to have it default to our scrollHeight.
Streamlit.setFrameHeight()
