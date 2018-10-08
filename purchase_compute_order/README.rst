=======================================================
Provide tools to help purchaser during purchase process
=======================================================

Functionnality :
----------------
    This module helps you to decide what you have to buy.

How To:
    * Create a new Compute Purchase Order (CPO)
    * Select a Supplier
    * Check the boxes to tell if you want to take into account the virtual
    stock or the draft sales/purchases
    * Use the button to import the list of products you can purchase to this
    supplier (ie: products that have a product_supplierinfo for this partner).
    It especially calculates for each product:
        * the quantity you have or will have;
        * the average_consumption, based on the stock moves created during
        last 365days;
        * the theorical duration of the stock, based on the precedent figures.

    * Unlink the products you don't want to buy anymore to this supplier
    (this only deletes the product_supplierinfo)
    *  Add new products you want to buy and link them
    (this creates a product_supplierinfo)
    * Modify any information about the products: supplier product_code,
    supplier product_name, purchase price, package quantity, purchase UoM.
    * Modify the calculated consumption if you think you'll sell more or
    less in the future.
    * Add a manual stock quantity (positive if you will receive products
    that are not registered at all in OE, negative if you have not registered
    sales)

    * Click the "Update Products" button to register the changes you've made
    into the product supplierinfo.
    * Check the Purchase Target. It's defined on the Partner form, but you
    still can change it on each CPO.
    * Click the button to calculate the quantities you should purchase. It
    will compute a purchase order fitting the purchase objective you set,
    trying to optimize the stock duration of all products.
    * Click the "Make Order" button to convert the calculation into a real
    purchase order.

Possible Improvements:
    * offer more options to calculate the average consumption;

Copyright, Author and Licence :
-------------------------------
    * Copyright : 2013-Today, Groupement Régional Alimentaire de Proximité;
    * Author :
        * Julien WESTE;
        * Sylvain LE GAL (https://twitter.com/legalsylvain);
    * Licence : AGPL-3 (http://www.gnu.org/licenses/)
