$(document).ready(function () {
    var button = $('.hamburger'),
        wrapper = $('#wrapper'),
        isClosed = button.hasClass('is-closed');

    button.click(function () {
        if (isClosed) {
            button.removeClass('is-closed');
            button.addClass('is-open');
            isClosed = false;
        } else {
            button.removeClass('is-open');
            button.addClass('is-closed');
            isClosed = true;
        }
        wrapper.toggleClass('toggled');
    });
});
