package fbvoting.chart.db;

import it.unimi.dsi.logging.ProgressLogger;

import java.util.Iterator;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.mongodb.BasicDBObject;
import com.mongodb.DBCollection;
import com.mongodb.DBCursor;
import com.mongodb.DBObject;

public class Delegates {
	
	private final static Logger LOGGER = LoggerFactory.getLogger(Delegates.class);
	
	private static DBCursor getOrderedCursorForGraph(Category category) {
		DBCollection collection = Db.getInstance().MONGODB.getCollection("graph");
		
		DBObject query = Db.excludingRemoved(category.query());
		DBObject returningFields = new BasicDBObject("from", 1).append("to", 1);
		DBCursor cursor = collection.find(query, returningFields);
		
		return cursor;
	}
	
	public static Iterator<long[]> getVotes(Category cat) {
		return new VoteIterator(cat);
	}
	
	private static class VoteIterator implements Iterator<long[]> {
		private DBCursor cursor;
		
		public VoteIterator(Category category) {
			cursor = getOrderedCursorForGraph(category);
		}

		public boolean hasNext() {
			return cursor.hasNext();
		}

		public long[] next() {
			DBObject item = cursor.next();
			return new long[] {
				((Number) item.get("from")).longValue() ,
				((Number) item.get("to")).longValue()	
			};
		}

		public void remove() {
			throw new UnsupportedOperationException();
		}
	}
	
	public static String getVotesAsString(Category cat) {
		
		DBCursor cursor = getOrderedCursorForGraph(cat);
		StringBuilder s = new StringBuilder();
		
		ProgressLogger progressLogger = new ProgressLogger(LOGGER, "votes");
		progressLogger.start();
		
		for (DBObject item : cursor) {
			s.append(item.get("from"))
			 .append('\t')
			 .append(item.get("to"))
			 .append('\n');
			
			progressLogger.lightUpdate();
		}
		
		progressLogger.done();
		
		return s.toString();
	}
	
}
