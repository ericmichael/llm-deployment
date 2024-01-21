import { Controller } from "stimulus"

export default class extends Controller {
  static targets = [ "input", "output" ]

  connect() {
    this.update()
  }

  update() {
    this.outputTarget.innerText = this.inputTarget.value
  }
}