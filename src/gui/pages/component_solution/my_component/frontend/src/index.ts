import { Streamlit, RenderData } from "streamlit-component-lib"
import { dataDict, initShiftPlanTable} from "./shift_plan_table.js"; // 

// TODO make simpler styles
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
    if (data.args["render_option"] == "shift_plan_solution") {
        let shift_plan_solution = JSON.parse(data.args["data"])
        let extra_options = JSON.parse(data.args["extra_options"])
        // Initialize the shift plan table with the provided solution data
        initShiftPlanTable(shift_plan_solution, extra_options["read_only"])
        if(extra_options["read_only"]){
        }
    }

    // We tell Streamlit to update our frameHeight after each render event, in
    // case it has changed. (This isn't strictly necessary for   the example
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
