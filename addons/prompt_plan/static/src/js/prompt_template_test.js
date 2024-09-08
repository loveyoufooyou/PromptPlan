/** @odoo-module **/

import { FormController } from "@web/views/form/form_controller";
import { onMounted, onWillUnmount } from "@odoo/owl";

export class TestFormController extends FormController {
    setup() {
        super.setup();
        console.log('setup')
        
        onMounted(() => {
            $(document).ready(() => {
                this._initializeTestNumber();
            });
            $('.test_number').on('input', this._onTestNumberInputChange.bind(this));
        });
        onWillUnmount(() => {
            $('.test_number').off('input');
        });
    }

    async _onTestNumberInputChange(event) {
        const inputElement = event.target;
        const inputValue = parseInt(inputElement.value, 10);
        console.log("Input value:", inputValue);

        if (isNaN(inputValue)) {
            inputElement.value = '';
            return;
        }
        if (inputValue < 1 || inputValue > 5) {
            inputElement.value = '';
            return;
        }
        for (let i = 1; i <= 5; i++) {
            const element = $(`.response${i}`);
            if (i <= inputValue) {
                element.css('display', '');
            } else {
                element.css('display', 'none');
            }
        }
    }

    _initializeTestNumber() {
        const inputElement = $('.test_number input')[0];
        const initialValue = parseInt(inputElement.value, 10);
        if (!isNaN(initialValue) && initialValue >= 1 && initialValue <= 5) {
            this._onTestNumberInputChange({ target: inputElement });
        }
    }
}
