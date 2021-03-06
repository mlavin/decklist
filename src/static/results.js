$(document).ready(function() {
    // Bind the card popovers
    $('[data-toggle="popover"]').popover();
    // Recalcuate totals and subtotals
    $('input[id$="-count"]').change(function () {
        var input = $(this),
            value = parseInt(input.val(), 10),
            quantity = input.data('quantity'),
            subtotalElement = $('#' + input.data('card') + '-subtotal'),
            price = subtotalElement.data('price'),
            remaining = Math.min(Math.max(quantity - value, 0), quantity),
            subTotal = parseFloat(price) * remaining,
            remainingTotal = 0,
            remainingCount = 0;
        // Show new subtotal
        input.data('remaining', remaining);
        subtotalElement.text(subTotal.toFixed(2));
        // Update cart form
        $('#' + input.data('card') + '-cart-quantity').val(remaining);
        $('#' + input.data('card') + '-cart-quantity').prop('disabled', remaining <= 0);
        $('#' + input.data('card') + '-cart-asin').prop('disabled', remaining <= 0);
        // Update totals
        $('[id$="-subtotal"]').each(function () {
            remainingTotal += parseFloat($(this).text());
        });
        $('[data-remaining]').each(function () {
            remainingCount += $(this).data('remaining');
        });
        $('#expected-cards').text(remainingCount);
        $('#expected-price').text(remainingTotal.toFixed(2));
    });

    // Sharing buttons
    function windowPopup(url, width, height) {
        // Calculate the position of the popup so
        // it’s centered on the screen.
        var left = (screen.width / 2) - (width / 2),
            top = (screen.height / 2) - (height / 2);

        window.open(url, '', 'menubar=no,toolbar=no,resizable=yes,scrollbars=yes,width=' +
                             width + ',height=' + height + ',top=' + top + ',left=' + left);
    }

    $('a[data-window]').on('click', function(e) {
        e.preventDefault();
        windowPopup($(this).attr('href'), 500, 300);
    });
});
