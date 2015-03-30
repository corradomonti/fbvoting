package fbvoting.chart.db;

import java.util.NoSuchElementException;

import com.mongodb.BasicDBObject;
import com.mongodb.DBCursor;
import com.mongodb.DBObject;

public class Category {
	public static Category[] getCategories() {
		DBCursor cursor = Db.getInstance().MONGODB.getCollection("categories").find();
		Category[] r = new Category[cursor.count()];
		int i = 0;
		for (DBObject item : cursor) {
			r[i++] = new Category(item);
		}
		return r;
	}
	
	public static Category[] findAll(String[] names) {
		Category[] result = new Category[names.length];
		for (int i = 0; i < names.length; i++)
			result[i] = find(names[i]);
		return result;
	}
	
	public static Category find(String name) {
		DBObject item = Db.getInstance().MONGODB
						.getCollection("categories")
						.findOne(new BasicDBObject("_id", name));
		
		if (item == null)
			throw new NoSuchElementException("Category '" + name + "' not found.");
		else
			return new Category(item);
 	}
	
	private String name;
	
	private Category(DBObject item) {
		this.name = item.get("_id").toString();
	}
	
	public String getName() {
		return name;
	}
	
	public BasicDBObject query() {
		return new BasicDBObject("category", this.getName());
	}
	
	public String toString() {
		return "Category '"+name+"'";
	}
	
}
