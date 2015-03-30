package fbvoting.chart.db;

import java.net.UnknownHostException;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.mongodb.BasicDBObject;
import com.mongodb.MongoClient;
import com.mongodb.MongoClientURI;

import fbvoting.chart.ConfReader;

public class Db {
	private final static Logger LOGGER = LoggerFactory.getLogger(Db.class);
	
	private static Db instance;
	public static Db getInstance() {
		if (instance == null)
			try {
				instance = new Db();
			} catch (UnknownHostException e) {
				throw new RuntimeException("Could not connect to MongoDb.", e);
			}
		
		return instance;
	}
	
	protected final static BasicDBObject excludingRemoved(BasicDBObject query) { 
		return query.append("rm", new BasicDBObject("$ne", true));
	}

	
	private final MongoClientURI MONGO_URI;
	protected final com.mongodb.DB MONGODB;
	
	private Db() throws UnknownHostException {
		MONGO_URI = new MongoClientURI(ConfReader.Field.MONGO_URI.value());
		LOGGER.info("Connecting to MongoDB...");
		MongoClient mongoClient = new MongoClient(MONGO_URI);
		LOGGER.info("MongoDB connection established.");
		MONGODB = mongoClient.getDB( MONGO_URI.getDatabase());
	}
	
	
	

}
