// chat/static/chat/js/controllers/thread_controller.js
import { Controller } from "stimulus"
import Idiomorph from 'idiomorph'
import Prism from 'prismjs';

export default class extends Controller {
  static targets = ["form", "messageList", "messageInput", "emptyMessage"]

  connect() {
    console.log("Connected to StimulusJS Thread Controller!")
    this.scrollToBottom()
  }

  submit(event) {
    event.preventDefault()

    // Remove "No messages yet" div if it exists
    if (this.hasEmptyMessageTarget) {
      this.emptyMessageTarget.remove()
    }

    // Add user's message to the message list
    this.messageListTarget.innerHTML += `
      <div class="flex gap-4 p-6 border-b border-gray-200 text-gray-800 bg-gray-50">
        <i class="fas fa-user w-6 text-lg text-green-400"></i>
        <div>${this.escapeHTML(this.messageInputTarget.value)}</div>
      </div>
    `

    // Display loading indicator
    this.messageListTarget.innerHTML += `
      <div class="flex gap-4 p-6 border-b border-gray-200 text-gray-800 bg-gray-50">
        <i class="fas fa-robot w-6 text-lg text-indigo-400"></i>
        <div role="status">
          <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-blue-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <span class="sr-only">Loading...</span>
        </div>
      </div>
    `

    // Scroll to the bottom
    this.scrollToBottom()

    // Submit the form via AJAX
    fetch(this.formTarget.action, {
      method: 'POST',
      body: new FormData(this.formTarget),
      headers: {
        'X-CSRFToken': this.formTarget.querySelector('[name=csrfmiddlewaretoken]').value
      }
    })
      .then(response => response.text())
      .then(html => {
        const parser = new DOMParser()
        const doc = parser.parseFromString(html, 'text/html')

        // Use idiomorph to only update the parts of the page that have changed
        Idiomorph.morph(document.body, doc.body)

        // Defer the scrolling until after the browser has rendered the updated DOM
        requestAnimationFrame(() => {
          Prism.highlightAll()
          this.scrollToBottom()
        })
      })

    // Clear out the textbox in the form
    this.messageInputTarget.value = ''
  }

  scrollToBottom() {
    this.messageListTarget.scrollTop = this.messageListTarget.scrollHeight
  }

  escapeHTML(str) {
    return str.replace(/[&<>'"]/g,
      tag => ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        "'": '&#39;',
        '"': '&quot;'
      }[tag] || tag));
  }
}