-- public.orders definition

-- Drop table

-- DROP TABLE public.orders;

CREATE TABLE IF NOT EXISTS public.orders (
	id bigserial NOT NULL,
	user_name varchar NULL,
	product_name varchar NULL,
	category varchar NULL,
	amount int4 NULL,
	status varchar NULL,
	order_date timestamp NULL,
	CONSTRAINT orders_pk PRIMARY KEY (id)
);