const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const [editorPath, offerPath] = process.argv.slice(2);
const editor = fs.readFileSync(editorPath, "utf8");
const offer = JSON.parse(fs.readFileSync(offerPath, "utf8"));

function block(tag, id) {
  const opening = '<' + tag + ' id="' + id + '">';
  const start = editor.indexOf(opening);
  const end = editor.indexOf('</' + tag + '>', start + opening.length);
  if (start < 0 || end < 0) throw new Error("Missing build section " + id);
  return editor.slice(start + opening.length, end);
}

const app = block("script", "app-script");
const browserStart = app.indexOf("// Browser event handlers");
if (browserStart < 0) throw new Error("Missing browser bindings");
const css = ["fonts", "proposal-style", "app-style"].map(id => block("style", id)).join("\n");
const context = vm.createContext({
  inegoOffer: offer,
  structuredClone,
  localStorage: { getItem: () => null },
  buildStyles: css,
  buildApp: app,
});

vm.runInContext([
  block("script", "catalog-script"),
  block("script", "visual-library-script"),
  app.slice(0, browserStart),
  "globalThis.builtClient = clientDocument(offer, buildStyles, buildApp);",
  "globalThis.builtReply = replyDocument(buildStyles, proposalHtml().replace(" +
    JSON.stringify('<article class="proposal">') + ", " +
    JSON.stringify('<article class="proposal"><p class="quote-note">Демонстрационный ответ · пример заполнения</p>') + "));",
].join("\n"), context, { filename: editorPath });

const output = path.dirname(editorPath);
fs.writeFileSync(path.join(output, "KP_INEGO_Suvorov_Client.html"), context.builtClient, "utf8");
fs.writeFileSync(path.join(output, "KP_INEGO_Suvorov_Reply_Example.html"), context.builtReply, "utf8");
console.log("Built editor, client offer and example reply.");
