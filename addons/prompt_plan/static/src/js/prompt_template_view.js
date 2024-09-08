/** @odoo-module **/

import { registry } from "@web/core/registry";
import { formView } from "@web/views/form/form_view";
import { TestFormController } from "./prompt_template_test";

export const TestFormView = {
    ...formView,
    Controller: TestFormController,
};

registry.category("views").add("prompt_template_test", TestFormView);
