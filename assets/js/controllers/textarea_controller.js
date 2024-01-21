// app/javascript/controllers/textarea_controller.js
import { Controller } from "stimulus"

export default class extends Controller {
  static targets = [ "input" ]

  connect() {
    console.log("connected to textarea controller");
    this.resize()
  }

  resize() {
    this.inputTarget.style.height = 'auto'
    var scrollHeight = this.inputTarget.scrollHeight
    if(scrollHeight<=40)
        this.inputTarget.style.height = `40px`
    else
        this.inputTarget.style.height = `${scrollHeight}px`
  }

  grow() {
    this.resize()
  }
}