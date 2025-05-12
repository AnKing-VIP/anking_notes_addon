require("anki/EditorField").lifecycle.onMount((field) => {
    (async () => {
        const occlusionCss = `
img {
  max-width: 100% !important;
  max-height: var(--anking-closet-max-height);
}

.anking-rect__rect {
  fill: moccasin;
  stroke: olive;
}

.is-active anking-rect__rect {
  fill: salmon;
  stroke: yellow;
}

.anking-rect__ellipsis {
  fill: transparent;
  stroke: transparent;
}

.anking-rect__label {
  stroke: black;
  stroke-width: 0.5;
}`;
        const fieldElement = await field.element;
        if (!fieldElement.hasAttribute("has-occlusion-style")) {
            const style = document.createElement("style");
            style.id = "anking-occlusion-style";
            style.rel = "stylesheet";
            style.textContent = occlusionCss;
            const richTextEditable = await EditorIO.get(
                field.editingArea.editingInputs
            ).find((input) => input.name === "rich-text").element;
            richTextEditable.getRootNode().prepend(style);

            fieldElement.setAttribute("has-occlusion-style", "");
        }
    })();
});

var EditorIO = {
    NoteEditor: require("anki/NoteEditor"),
    get: require("svelte/store").get,
    imageSrcPattern: /^https?:\/\/(?:localhost|127.0.0.1):\d+\/(.*)$/u,

    focusIndex: 0,
    occlusionMode: false,
    occlusionField: null,
    occlusionEditorTarget: null,
    getOcclusionButton: () => document.getElementById("ankingOcclude"),

    /** tweening **/
    rushInOut: (x) => {
        return 2.388 * x - 4.166 * Math.pow(x, 2) + 2.77 * Math.pow(x, 3);
    },

    /** Python functions moved to JS for async operations **/
    escapeJSText: (text) => {
        return text
            .replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("'", "\\'");
    },

    getFocusedFieldIndex: () => {
        if (document.activeElement.classList.contains("rich-text-editable")) {
            return [...document.querySelector(".fields").children].indexOf(
                document.activeElement.closest(".editor-field").parentNode
            );
        } else return 0;
    },

    replaceOrPrefixOldOcclusionText: (oldHTML, newText) => {
        const occlusionBlockRegex = /\[#!occlusions.*?#\]/;

        const newHTML = newText.split(/\r?\n/).join("<br>");
        replacement = `[#!occlusions ${newHTML} #]`;

        /** imitate re.subn **/
        [subbed, numberOfSubs] = ((count = 0) => {
            const subbed = oldHTML.replace(occlusionBlockRegex, () => {
                ++count;
                return replacement;
            });
            return [subbed, count];
        })();

        if (numberOfSubs > 0) {
            return subbed;
        } else if (["", "<br>"].includes(oldHTML)) {
            return replacement;
        } else {
            return `${replacement}<br>${oldHTML}`;
        }
    },

    setActive: (target) => {
        EditorIO.occlusionEditorTarget = target;
        EditorIO.occlusionMode = true;
        EditorIO.getOcclusionButton().classList.add("highlighted");
        bridgeCommand("ankingOcclusionEditorActive");
    },

    setInactive: () => {
        EditorIO.occlusionEditorTarget = null;
        EditorIO.occlusionMode = false;
        EditorIO.getOcclusionButton().classList.remove("highlighted");
        bridgeCommand("ankingOcclusionEditorInactive");
    },

    getFieldHTML: async (index) => {
        const richTextEditable = await EditorIO.getRichTextEditable(index);
        return richTextEditable.innerHTML;
    },

    setFieldHTML: async (index, html) => {
        const richTextEditable = await EditorIO.getRichTextEditable(index);
        richTextEditable.innerHTML = html;
    },

    getRichTextEditable: async (index) => {
        return await EditorIO.get(
            EditorIO.NoteEditor.instances[0].fields[index].editingArea
                .editingInputs
        ).find((input) => input.name === "rich-text").element;
    },

    setupOcclusionEditor: async (closet, maxOcclusions) => {
        const elements = ["[[makeOcclusions]]"];
        let fieldFound = false;

        for (const field of EditorIO.NoteEditor.instances[0].fields) {
            const richTextInputAPI = EditorIO.get(
                field.editingArea.editingInputs
            ).find((input) => input.name === "rich-text");

            const richTextEditable = await richTextInputAPI.element;

            if (!fieldFound) {
                let images = richTextEditable.querySelectorAll("img");

                if (images.length && !fieldFound) {
                    if (images.length > 1) {
                        bridgeCommand("ankingClosetMultipleImages");
                        return;
                    }
                    EditorIO.occlusionField = {
                        editingArea: field.editingArea,
                        callback: richTextInputAPI.preventResubscription(),
                    };
                    fieldFound = true;
                    field.editingArea.refocus();
                }
            }
            elements.push(richTextEditable);
        }

        const acceptHandler = (_entry, internals) => (shapes, draw) => {
            const imageSrc = draw.image.src.match(EditorIO.imageSrcPattern)[1];

            const newIndices = [
                ...new Set(
                    shapes
                        .map((shape) => shape.labelText)
                        .map((label) =>
                            label.match(closet.patterns.keySeparation)
                        )
                        .filter((match) => match)
                        .map((match) => Number(match[2]))
                        .filter((maybeNumber) => !Number.isNaN(maybeNumber))
                ),
            ];

            bridgeCommand(
                `ankingNewOcclusions:${imageSrc}:${newIndices.join(",")}`
            );

            const shapeText = shapes
                .map((shape) =>
                    shape.toText(internals.template.parser.delimiters)
                )
                .join("\n");

            bridgeCommand(`ankingOcclusionText:${shapeText}`);

            EditorIO.clearOcclusionMode();
        };

        const setupOcclusionMenu = (menu) => {
            menu.splice(1, 0, {
                label: `<input
                    type="range"
                    min="1"
                    max="100"
                    value="${EditorIO.maxHeightPercent}"
                    oninput="EditorIO.handleMaxHeightChange(window.event)"
                />`,
                html: true,
            });

            return menu;
        };

        const existingShapesFilter = () => (shapeDefs, draw) => {
            const indices = [
                ...new Set(
                    shapeDefs
                        .map((shape) => shape[2])
                        .map((label) =>
                            label.match(closet.patterns.keySeparation)
                        )
                        .filter((match) => match)
                        .map((match) => Number(match[2]))
                        .filter((maybeNumber) => !Number.isNaN(maybeNumber))
                ),
            ];

            const imageSrc = draw.image.src.match(EditorIO.imageSrcPattern)[1];
            bridgeCommand(
                `ankingOldOcclusions:${imageSrc}:${indices.join(",")}`
            );

            return shapeDefs;
        };

        const editorOcclusion = closet.browser.recipes.occlusionEditor({
            maxOcclusions,
            acceptHandler,
            setupOcclusionMenu,
            existingShapesFilter,
        });

        const filterManager = closet.FilterManager.make();
        const target = editorOcclusion(filterManager.registrar);

        filterManager.install(
            ...["rect", "recth", "rectr"].map((tagname) =>
                closet.browser.recipes.rect.hide({ tagname })
            )
        );

        closet.template.BrowserTemplate.makeFromNodes(elements).render(
            filterManager
        );

        EditorIO.setActive(target);
    },

    clearOcclusionMode: async () => {
        if (EditorIO.occlusionMode) {
            EditorIO.occlusionEditorTarget.dispatchEvent(new Event("reject"));

            setTimeout(() => {
                EditorIO.occlusionField.callback.call();
            })
            EditorIO.focusIndex = EditorIO.getFocusedFieldIndex();

            EditorIO.hadOcclusionEditor = true;
            EditorIO.setInactive();
        }
    },

    maybeRefocus: () => {
        if (EditorIO.hadOcclusionEditor) {
            bridgeCommand("ankingClosetRefocus");
            EditorIO.hadOcclusionEditor = false;
        }
    },

    refocus: () => {
        if (EditorIO.occlusionField) {
            EditorIO.occlusionField.editingArea.refocus();
        }
    },

    // is what is called from the UI
    toggleOcclusionMode: (jsPath, maxOcclusions) => {
        if (EditorIO.occlusionMode) {
            EditorIO.clearOcclusionMode();
        } else {
            import(`/${jsPath}`).then(
                (closet) =>
                    EditorIO.setupOcclusionEditor(closet, maxOcclusions),
                (error) => console.log("Could not load AnKing Closet:", error)
            );
        }
    },

    insertIntoZeroIndexed: async (newText, index) => {
        const oldHTML = await EditorIO.getFieldHTML(index);
        const text = EditorIO.replaceOrPrefixOldOcclusionText(oldHTML, newText);

        const escaped = EditorIO.escapeJSText(text);

        pycmd(`key:${index}:${getNoteId()}:${escaped}`);
        EditorIO.setFieldHTML(index, escaped);
    },

    /**************** MAX HEIGHT *****************/
    handleMaxHeightChange: (event) => {
        EditorIO.setMaxHeightPercent(Number(event.currentTarget.value));
    },

    maxHeightPercent: 0,
    setMaxHeightPercent: (value /* 1 <= x <= 100 */) => {
        const maxMaxHeight = globalThis.screen.height;
        const factor = EditorIO.rushInOut(value / 100);

        EditorIO.maxHeightPercent = value;
        EditorIO.setMaxHeight(factor * maxMaxHeight);
    },

    setMaxHeight: (value /* > 0 */) => {
        document.documentElement.style.setProperty(
            "--anking-closet-max-height",
            `${value}px`
        );
    },
};
