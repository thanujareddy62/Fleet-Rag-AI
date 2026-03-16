document.addEventListener("DOMContentLoaded", function () {

    const chatBox = document.getElementById("chatBox");
    const typing = document.getElementById("typing");
    const form = document.getElementById("chatForm");

    // scroll chat to bottom
    function scrollToBottom() {
        if (chatBox) {
            chatBox.scrollTo({
                top: chatBox.scrollHeight,
                behavior: "smooth"
            });
        }
    }

    scrollToBottom();

    // syntax highlighting
    if (typeof hljs !== "undefined") {
        hljs.highlightAll();
    }

    // show typing indicator
    if (form) {
        form.addEventListener("submit", function () {
            if (typing) {
                typing.style.display = "block";
            }
        });
    }

});

// copy text
function copyText(id) {

    const text = document.getElementById(id).innerText;

    navigator.clipboard.writeText(text);

}
