import { env } from "process";
import * as esbuild from "esbuild";
import fs from "fs";

function getVersion() {
    return fs.readFileSync(".version", { encoding: "utf8", flag: "r" });
}

const production = env.NODE_ENV === "production";
const development = env.NODE_ENV === "development";

const entryPoints = ["src/index.ts"];

const options = {
    entryPoints,
    outfile: `../src/anking_notetypes/resources/__ankingio-${getVersion()}.js`,
    format: "esm",
    target: "es6",
    bundle: true,
    minify: production,
    treeShaking: production,
    sourcemap: !production,
    pure: production ? ["console.log", "console.time", "console.timeEnd"] : [],
    loader: {
        ".png": "dataurl",
        ".svg": "text",
    },
};

const context = await esbuild.context(options);

if (development) {
    console.log("Watching for changes...");
    await context.watch();
} else {
    await context.rebuild();
    context.dispose();
}
