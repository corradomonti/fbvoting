package fbvoting.chart.db;

import it.unimi.dsi.fastutil.longs.Long2DoubleMap;
import it.unimi.dsi.fastutil.objects.Object2DoubleMap.Entry;
import it.unimi.dsi.fastutil.objects.Object2DoubleOpenHashMap;
import it.unimi.dsi.logging.ProgressLogger;

import java.util.Map;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.mongodb.BasicDBObject;
import com.mongodb.DBCollection;
import com.mongodb.DBCursor;
import com.mongodb.DBObject;


public class ItemRanker {
	private final static Logger LOGGER = LoggerFactory.getLogger(ItemRanker.class);
	
	private Category category;
	private DBCursor cursor;
	private Object2DoubleOpenHashMap<VotableItem> itemRanks;

	
	public ItemRanker(Category category) {
		this.category = category;
		DBCollection collection = Db.getInstance().MONGODB.getCollection("advices");
		DBObject query = Db.excludingRemoved(category.query());
		cursor = collection.find(query);
	}
	
	public ItemRanker apply(Long2DoubleMap idToRank) {
		
		LOGGER.info("Applying user rankings to advices given by users...");
		
		itemRanks = new Object2DoubleOpenHashMap<VotableItem>();
		itemRanks.defaultReturnValue(0);
		ProgressLogger progressLogger = new ProgressLogger(LOGGER, "advices");
		progressLogger.start();
		
		for (DBObject document : cursor) {
			long userId = ((Number) document.get("user")).longValue(); // since you cannot cast Integer to Long.
			double userRank = idToRank.get(userId);
			
			VotableItem item = VotableItem.from((DBObject) document.get("advice")); 
			itemRanks.addTo(item, userRank);
			
			progressLogger.lightUpdate();
		}
		
		progressLogger.done();
		
		return this;
	}
	
	public ItemRanker findMaxNormAndSaveIt() {
		LOGGER.info("Finding normalization factor...");
		
		double maxNorm = 0;
		for (double score : itemRanks.values())
			if (score > maxNorm)
				maxNorm = score;
		
		LOGGER.info("Saving normalization factor for " + category + ": " + maxNorm);
		DBCollection collection = Db.getInstance().MONGODB.getCollection("chartnorm");
		BasicDBObject oldObjectId = new BasicDBObject("_id", category.getName());
		BasicDBObject newObject = new BasicDBObject(oldObjectId).append( "norm", maxNorm );
		collection.update( oldObjectId, newObject, true, false );
		return this;
	}
	
	public ItemRanker save() {
		
		String collectionName = "chart-" + category.getName();
		LOGGER.info("Saving the final chart on MongoDB as " + collectionName
				+ " (removing any previous chart)...");
		
		DBCollection collection = Db.getInstance().MONGODB.getCollection(collectionName);
		collection.drop();
		
		for (Entry<VotableItem> itemRank: itemRanks.object2DoubleEntrySet()) {
			try {
				DBObject document = new BasicDBObject("advice", itemRank.getKey().toDBObject())
										.append("rank", itemRank.getDoubleValue());
				collection.insert(document);
			} catch (VotableItem.NoVideoAssociatedException e) {
				LOGGER.error(itemRank.getKey() + " do not have an associated video," +
						"and will be excluded from results.");
			}
		}
		
		LOGGER.info(collectionName + " saved. Creating index...");
		
		collection.createIndex(new BasicDBObject("rank", -1).append("_id", 1));
		
		LOGGER.info("Index on " + collectionName + " has been created.");
		
		return this;
	}
	
	

}
