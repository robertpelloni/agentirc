with open('public/style.css', 'a') as f:
    f.write("""
/* Hide user avatar completely and tighten message spacing */
.message-row {
    padding-top: 0px !important;
    padding-bottom: 0px !important;
}

.message-avatar {
    display: none !important;
}

.step {
    padding: 2px !important;
    margin: 0 !important;
}

.message-author {
    color: #ff00ff !important;
    font-weight: bold !important;
}

.message-author::before {
    content: "<";
    color: #c0c0c0;
}

.message-author::after {
    content: ">";
    color: #c0c0c0;
}

.message-row[data-author="system"] .message-author::before {
    content: "* ";
}

.message-row[data-author="system"] .message-author::after {
    content: "";
}

.message-row[data-author="system"] .message-author {
    color: #00ff00 !important;
}

""")
