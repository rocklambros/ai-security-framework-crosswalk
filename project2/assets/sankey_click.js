/**
 * Attach a plotly_click handler to the Sankey graph that writes every click
 * (including repeated clicks on the same link/node) to a dcc.Store via
 * dash_clientside.set_props.  Dash's built-in clickData prop does NOT fire
 * when the user clicks the same element twice because the value doesn't
 * change, so we add a monotonic counter to guarantee uniqueness.
 */
(function () {
    "use strict";

    var GRAPH_ID = "explorer-sankey";
    var STORE_ID = "explorer-sankey-click-store";
    var _counter = 0;
    var _bound = false;

    function attach() {
        var wrapper = document.getElementById(GRAPH_ID);
        if (!wrapper) return;
        var plotDiv = wrapper.querySelector(".js-plotly-plot");
        if (!plotDiv || !plotDiv.on) return;
        if (_bound) return;

        plotDiv.on("plotly_click", function (eventData) {
            if (!eventData || !eventData.points || !eventData.points.length) return;
            _counter += 1;
            var pt = eventData.points[0];
            var payload = {
                n: _counter,
                customdata: pt.customdata || null,
                label: pt.label || null,
                targetCustomdata: (pt.target && pt.target.customdata) ? pt.target.customdata : null,
                targetLabel: (pt.target && pt.target.label) ? pt.target.label : null,
            };
            if (window.dash_clientside && window.dash_clientside.set_props) {
                window.dash_clientside.set_props(STORE_ID, { data: payload });
            }
        });
        _bound = true;
    }

    // Re-attach after Dash hot-reloads or renders the graph
    var observer = new MutationObserver(function () {
        if (!_bound) attach();
    });
    observer.observe(document.body, { childList: true, subtree: true });

    // Initial attempt
    if (document.readyState === "complete") {
        attach();
    } else {
        window.addEventListener("load", attach);
    }
})();
