const fs = require("fs");
const path = require("path");
const sass = require("sass");

const __basedir = `${__dirname}/..`;

const getVersion = () => {
    return fs.readFileSync(`${__basedir}/.version`, { encoding: 'utf8', flag: 'r' }).trim();
}
const renderFile = (input, output) => {
    sass.render(
        {
            file: input,
        },
        (error, result) => {
            if (error) {
                console.error(error);
                return;
            }

            fs.writeFile(output, result.css, (error) => {
                if (error) {
                    return console.log(error);
                }

                console.log(`SCSS was successfully compiled to ${output}`);
            });
        },
    );
};

renderFile(
    path.join(__basedir, "style", "editor.scss"),
    `${__basedir}/../src/anking_notetypes/web/editor.css`,
);

renderFile(
    path.join(__basedir, "style", "base.scss"),
    `${__basedir}/../src/anking_notetypes/resources/__ankingio-${getVersion()}.css`,
);
