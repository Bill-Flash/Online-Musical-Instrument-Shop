# Online Musical Instrument Shop

## Problem Statement
My software engineering team has been hired to meet the needs of a client, a local Musical Instrument Shop. This shop is family-owned and has sold musical instruments locally for years. All of their business to-date is walk-in retail customers.

Due to the pandemic almost all sales have gone online and the shop has so far not entered the online market. They would like to enter this market with a new website. They would also like a new name and image online.

Their main requirements are:

* Ease of use for customers and their staff
	* Quality communication between them and their customers
	* The ability for users and employees to interface with the new solution in English or Chinese
* The website should have two portals
* 	A public customer portal that has 
	*  The company profile, “about us”, etc.
	*  A way to communicate with the company
	*  The shop products for sale
		*  Musical Instrument selection
		*  Services (like pickup, delivery, etc.)
	*  A way to place orders (pickup / delivery, etc.)
	*  A way to modify existing orders that are not yet complete
	*  A way to see order status
*  A staff portal that can
	*  Allow employees to organize, modify, prioritize, update and keep track of orders in the system including adding new items for sale.
	*  Change any part of how sales are handled due to the pandemic. For instance, if the physical shop closes, collection is no longer possible.
	*  See and respond to communications from customers.

## User Guide
If you would like to use our website, please refer to [User Document](./user.pdf).

## Maintainer Guide
If you would like to develop websites based on our website, please refer to [System Document](./system.pdf) to know the related architecture.


## Configure the environment

1. Create a Virtual Environment
2. Enter the Virtual Environment
3. Go to the requirements.txt directory and use the following command to import all required packages in the environment:
```
    pip install -r requirements.txt
```  

## Database Migration

1. Changes happened in models
2. Perform the migration command
```
    python manager.py db migrate -m "your message"
```
3. Perform the upgrade command
```
    python manager.py db upgrade
```

## Account for test

1. Staff
```
    username: 1234567
    password: 12345678
```
2. Customer
```
    username: bjjjjjj
    password: bqhbqhbqh
```

