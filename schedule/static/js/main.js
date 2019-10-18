function inputScrollToView(target) {
    if (/Mobi|Android/i.test(navigator.userAgent)) {
        target.scrollIntoView();
        window.scrollBy(0, -50);
    }
}
