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
        // Update totals
        $('[id$="-subtotal"]').each(function () {
            remainingTotal += parseFloat($(this).text());
        });
        $('[data-remaining]').each(function () {
            remainingCount += $(this).data('remaining');
        });
        $('#expected-cards').text(remainingCount);
        $('#expected-price').text(remainingTotal.toFixed(2));
        // TODO: Update cart form
    });
});
