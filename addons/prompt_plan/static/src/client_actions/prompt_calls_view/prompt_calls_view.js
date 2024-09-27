/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState } from "@odoo/owl";
import { ConfirmationDialog, AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

export class PromptCallsView extends Component {
    static template = "prompt_plan.prompt_calls_view_template";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
        this.dialog = useService("dialog");
        this.state = useState({
            fetchedDatas: {},
            contrast: false
        });

        let { active_id, active_model, context } = this.props.action.context;
        if (!active_id) {
            return;
        }
        if (!active_model) {
            active_model = 'prompt.template.test';
        }
        this.context = context || {};
        Object.assign(this.context, {
            active_id: active_id || this.props.action.params.active_id,
            model: active_model || false,
        });

        this.loadFetchedData();
    }

    async loadFetchedData() {
        const active_id = this.context.active_id;
        if (!active_id) {
            return;
        };
        const testElement = $(".test_number input")[0];
        if (!testElement) {
            this.dialog.add(ConfirmationDialog, {
                title: _t("Error"),
                body: _t("Error to get test number, please return to the test screen."),
                confirm: () => {
                    if (window.history.length > 1) {
                        window.history.back();
                    }
                },
                confirmLabel: _t("Previous Page"),
                cancel: () => { },
                cancelLabel: _t("Discard"),
            });
            return;
        }
        const testValue = parseInt(testElement.value, 10);
        let searchFields = ["input"]
        Object.assign(this.context, {
            test_number: testValue,
        });
        if (!isNaN(testValue) && testValue >= 1 && testValue <= 5) {
            for (let i = 1; i <= testValue; i++) {
                searchFields.push(`response${i}`, `score${i}`, `check${i}`);
            }
        };

        const [fetchedDatas] = await this.orm.read(
            "prompt.template.test",
            [active_id],
            searchFields,
        );
        const input = fetchedDatas["input"];
        let input_part = "";
        if (input && input.length > 20) {
            input_part = input.substr(0, 17) + "...";
        } else {
            input_part = input;
        }
        const extractedData = [];
        searchFields.forEach(key => {
            if (key.startsWith("response")) {
                const index = key.slice(8); // 提取数字部分
                const scoreKey = `score${index}`;
                const checkKey = `check${index}`;

                if (fetchedDatas.hasOwnProperty(scoreKey)) {
                    const newItem = {
                        index: index,
                        response: fetchedDatas[key],
                        score: fetchedDatas[scoreKey],
                        check: fetchedDatas[checkKey]
                    };
                    extractedData.push(newItem);
                }
            }
        });
        Object.assign(this.state, {
            fetchedDatas: extractedData, input: input, input_part: input_part
        });
        Object.assign(this.context, {
            fetchedDatas: extractedData
        });
    }

    async saveScore() {
        const active_id = this.context.active_id;
        const model = this.context.model;
        const testValue = this.context.test_number;
        let updateVals = {}
        let response_indexes = [];
        for (let i = 1; i <= testValue; i++) {
            let scoreKey = `score${i}`;
            let score = $(`#${scoreKey}`).val();
            if (score == "false") {
                score = false;
            }
            let origin_score = this.state.fetchedDatas[i - 1]['score']
            let origin_check = this.state.fetchedDatas[i - 1]['check']
            if (score && score != origin_score && origin_check) {
                updateVals[scoreKey] = score;
                response_indexes.push(i);
            }
        }
        if (Object.keys(updateVals).length != 0) {
            try {
                await this.orm.write(model, [active_id], updateVals);
                const action = await this.orm.call(model, "save_call_multi", [[active_id]],
                    { context: { response_indexes: response_indexes } }
                );
                for (const key in updateVals) {
                    let index = key.slice(5);
                    this.state.fetchedDatas[index - 1]['score'] = updateVals[key];
                }
                this.action.doAction(action);
            } catch (e) {
                this.dialog.add(AlertDialog, {
                    title: _t("Error"),
                    body: e.message,
                });
                return;
            }
            window.location = window.location;
        }
    }

    contrastModel() {
        if (!this.context.activeIndex) {
            this.dialog.add(AlertDialog, {
                title: _t("Configuration"),
                body: _t("Please select a tag first."),
            });
            return;
        }
        let $selects = $('select[name="Score"]');
        for (let i = 0; i < $selects.length; i++) {
            let $select = $($selects[i]);
            if (i === 0) {
                /* Set the first value to the next occurrence; otherwise,
                   if it is not the first value, the template will be re-rendered. */
                let firstVal = this.state.fetchedDatas[this.context.activeIndex - 1]['score'];
                $select.val(firstVal);
            }
        }
        Object.assign(this.state, {
            contrast: true,
            activeIndex: this.context.activeIndex
        });
    }

    aciveTag(i) {
        Object.assign(this.context, {
            activeIndex: i
        });
        if (this.state.contrast) {
            this.contrastModel();
            return;
        }
        // remove active style
        const classes = ['prompt-calls-show-active', 'prompt-score-active', 'prompt-score-select-active', 'prompt-tag-active'];
        classes.forEach(function (cls) {
            let x = `.${cls}`;
            $(x).removeClass(cls);
        });

        // add active style
        const templateTag = `#prompt-tmplate${i}`
        const scoreTemplateTag = `#score-tmplate${i}`
        const socreSelectTag = `#score${i}`
        const scoreButtonTag = `#tag${i}`
        $(templateTag).addClass('prompt-calls-show-active');
        $(scoreTemplateTag).addClass('prompt-score-active');
        $(socreSelectTag).addClass('prompt-score-select-active');
        $(scoreButtonTag).addClass('prompt-tag-active');
    }

    deactiveContrastModel() {
        Object.assign(this.state, {
            contrast: false
        });
    }

    showTagResponse() {
        $(".prompt-calls-show-active").addClass("show-tag-response");
    }

    dontShowTagResponse() {
        $(".prompt-calls-show-active").removeClass("show-tag-response");
    }

}

registry.category("actions").add("prompt_calls_view_tag", PromptCallsView);
