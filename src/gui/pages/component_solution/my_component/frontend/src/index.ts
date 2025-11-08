import { Streamlit, RenderData } from "streamlit-component-lib"
// does the order matter?
import "./shift_plan_config.js"; // this will be ran when imported
import shiftPlanTable, { initShiftPlanTable } from "./shift_plan_table.js"; // 
// Add text and a button to the DOM. (You could also add these directly
// to index.html.)
const span = document.body.appendChild(document.createElement("span"))
const textNode = span.appendChild(document.createTextNode(""))
const button = span.appendChild(document.createElement("button"))
button.textContent = "Click Me!"

// Add a click handler to our button. It will send data back to Streamlit.
let numClicks = 0
let isFocused = false
button.onclick = function (): void {
  // Increment numClicks, and pass the new value back to
  // Streamlit via `Streamlit.setComponentValue`.
  numClicks += 1
  Streamlit.setComponentValue(numClicks)
}

button.onfocus = function (): void {
  isFocused = true
}

button.onblur = function (): void {
  isFocused = false
}

/**
 * The component's render function. This will be called immediately after
 * the component is initially loaded, and then again every time the
 * component gets new data from Python.
 */
function onRender(event: Event): void {
  // Get the RenderData from the event
  const data = (event as CustomEvent<RenderData>).detail

  // Maintain compatibility with older versions of Streamlit that don't send
  // a theme object.
  if (data.theme) {
    // Use CSS vars to style our button border. Alternatively, the theme style
    // is defined in the data.theme object.
    const borderStyling = `1px solid var(${
      isFocused ? "--primary-color" : "gray"
    })`
    button.style.border = borderStyling
    button.style.outline = borderStyling
  }

  // Disable our button if necessary.
  button.disabled = data.disabled

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
  }

  // Show "Hello, name!" with a non-breaking space afterwards.
  textNode.textContent = `Hello, ${name}! ` + String.fromCharCode(160)

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
