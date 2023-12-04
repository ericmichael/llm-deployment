import { Application } from "stimulus"
import { definitionsFromContext } from "stimulus/webpack-helpers"
import Prism from 'prismjs';

const application = Application.start();
const context = require.context("./controllers", true, /\.js$/)
application.load(definitionsFromContext(context))

// Import and register all TailwindCSS Components or just the ones you need
import { Alert, Autosave, ColorPreview, Dropdown, Modal, Tabs, Popover, Toggle, Slideover } from "tailwindcss-stimulus-components"
application.register('alert', Alert)
application.register('autosave', Autosave)
application.register('color-preview', ColorPreview)
application.register('dropdown', Dropdown)
application.register('modal', Modal)
application.register('popover', Popover)
application.register('slideover', Slideover)
application.register('tabs', Tabs)
application.register('toggle', Toggle)

document.addEventListener('DOMContentLoaded', (event) => {
    console.log("Hello World.")
    Prism.highlightAll();
});