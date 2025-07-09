SELECT * FROM pg_trigger WHERE tgrelid = 'orders'::regclass;
SELECT status FROM orders WHERE id = 2;
SELECT pg_get_functiondef(oid)
FROM pg_proc
WHERE proname = 'create_right_on_order';
select * from rights where user_id = '158';
select * from users where id = '158';


CREATE OR REPLACE FUNCTION create_right_on_order()
RETURNS TRIGGER AS $$
BEGIN
  IF LOWER(NEW.status) = 'paid' THEN
    INSERT INTO rights (
      user_id, lock_id, access_type, access_value, valid_from, valid_until
    ) VALUES (
      NEW.user_id,
      5716380,  -- vagy config LOCK_ID
      'passcode',
      NEW.passcode,
      NOW(),
      NOW() + INTERVAL '30 days'
    );
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;


DROP TRIGGER IF EXISTS trg_order_to_right ON orders;

CREATE TRIGGER trg_order_to_right
AFTER INSERT ON orders
FOR EACH ROW
EXECUTE FUNCTION create_right_on_order();
